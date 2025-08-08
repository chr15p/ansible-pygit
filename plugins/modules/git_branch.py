#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# MIT License (see LICENSE)

DOCUMENTATION = r'''
---
module: git_branch
short_description: Create or delete a Git branch
description: Adds or deletes a local Git branch by name. Idempotent and safe to run repeatedly.
options:
  repo:
    description: Path on the filesystem to the Git repository worktree
    type: path
    required: true
  action:
    description: Whether to add or delete the branch
    type: string
    required: false
    choices: [add, delete]
    default: add
  parent:
    description: Branch or commit to branch from when creating a branch
    type: string
    required: false
    default: master
    aliases: [branch]
  name:
    description: Name of the branch to create or delete
    type: string
    required: true
'''

EXAMPLES = r'''
- name: Create a branch from master
  git_branch:
    repo: /path/to/repo
    action: add
    parent: master
    name: feature/foo

- name: Delete a branch
  git_branch:
    repo: /path/to/repo
    action: delete
    name: feature/foo
'''

RETURN = r'''
changed:
  description: Whether any change was made
  type: bool
message:
  description: A human-readable message
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import (
    normalize_path,
    open_repository,
    resolve_commit,
)

module_args = {
    "repo": {"type": 'path', "required": True},
    "action": {"type": 'str', "required": False, "choices": ['add', 'delete'], "default": 'add'},
    "parent": {"type": 'str', "required": False, "default": "master", "aliases": ['branch']},
    "name": {"type": 'str', "required": True},
}

def run_module():
    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    repo = module.params.get('repo')
    action = module.params.get('action')
    parent = module.params.get('parent')
    name = module.params.get('name')

    if action == 'delete':
        if name is None:
            AnsibleModule.fail_json(msg="Name is required when deleting a branch")

    try:
        repo_ref = open_repository(normalize_path(repo))
    except pygit2.GitError as e:
        module.fail_json(msg=f"failed to get repo at {repo}", exception=str(e))

    # Ensure index is loaded
    repo_ref.index.read()

    # Check if branch exists
    branch_obj = repo_ref.lookup_branch(name)

    if action == 'delete':
        if branch_obj is None:
            result['message'] = f"branch {name} does not exist"
            module.exit_json(**result)
        if module.check_mode:
            result['message'] = f"would delete branch {name}"
            module.exit_json(**result)
        branch_obj.delete()
        result['message'] = f"branch {name} deleted"
        result['changed'] = True
        module.exit_json(**result)

    # action == 'add'
    if branch_obj is not None:
        result['message'] = f"branch {name} already exists"
        module.exit_json(**result)

    # Resolve parent commit to branch from
    parent_commit = resolve_commit(repo_ref, parent)
    if parent_commit is None:
        module.fail_json(msg=f"{parent} not found in {repo}")

    if module.check_mode:
        result['message'] = f"would create branch {name} from {parent}"
        module.exit_json(**result)

    repo_ref.create_branch(name, parent_commit)
    result['message'] = f"branch {name} created"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
