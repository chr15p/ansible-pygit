#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# MIT License (see LICENSE)

from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import (
    get_wt_changes,
    get_status,
    open_repository,
    relativize_path,
    normalize_path
)

DOCUMENTATION = r'''
---
module: git_add
short_description: Stage one or more files in a Git repository
description: Stage files that have working tree changes in a Git repository. Idempotent; unchanged files are ignored.
options:
  repo:
    description: Path on the filesystem to the Git repository worktree
    type: path
    required: true
  files:
    description: List of file paths to stage. Paths may be absolute (inside the worktree) or relative to the worktree.
    type: list
    required: true
'''

EXAMPLES = r'''
 - name: Stage two files
   git_add:
     repo: /home/example/projects/test_repo
     files:
     - test_file1
     - test_file2
'''

RETURN = r'''
added_files:
  description: The list of files staged by this task (relative to the worktree)
  type: list
status:
  description: A dict with the files currently staged for commit as keys and their statuses as the values
  type: dict
ignored_files:
  description: Files that were ignored because they are outside the repository or had no working tree changes
  type: list
changed:
  description: Whether any change was made
  type: bool
message:
  description: A human-readable message
  type: str
'''



# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'path', "required": True},
    "files": {"type": "list", "required": True},
}


def run_module():

    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
        "added_files": [],
        "ignored_files": [],
        "status": {},
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    repo = module.params.get('repo')
    files = module.params.get('files')

    try:
        repo_ref = open_repository(normalize_path(repo))
    except pygit2.GitError as e:
        module.fail_json(msg=f"failed to get repo at {repo}", exception=str(e))

    index = repo_ref.index

    working_tree_changes = get_wt_changes(repo_ref)

    to_stage: list[str] = []
    ignored: list[str] = []

    for provided_path in files:
        is_inside, abs_path, rel_path = relativize_path(repo_ref, provided_path)
        if not is_inside:
            # outside the repo; ignore
            ignored.append(provided_path)
            continue
        if working_tree_changes.get(rel_path):
            to_stage.append(rel_path)
        else:
            ignored.append(provided_path)

    if module.check_mode:
        if to_stage:
            result['message'] = f"would stage {','.join(to_stage)} for commit"
            result['changed'] = False
            result['ignored_files'] = ignored
            result['status'] = get_status(repo_ref)
            module.exit_json(**result)
        else:
            result['message'] = "no new files added for commit"
            result['ignored_files'] = ignored
            result['status'] = get_status(repo_ref)
            module.exit_json(**result)

    if to_stage:
        for rel_path in to_stage:
            index.add(rel_path)
        index.write()

    result['status'] = get_status(repo_ref)

    if not to_stage:
        result['message'] = "no new files added for commit"
        result['ignored_files'] = ignored
    else:
        result['added_files'] = to_stage
        result['ignored_files'] = ignored
        result['message'] = f"staged {','.join(to_stage)} for commit"
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
