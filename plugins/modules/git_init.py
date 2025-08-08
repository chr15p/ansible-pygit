#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#from __future__ import (absolute_import, division, print_function)
#__metaclass__ = type


import pygit2
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pygit_utils import open_repository, normalize_path


DOCUMENTATION = r'''
---
module: git_init
short_description: Initialize a new Git repository (bare or non-bare)
description: Initialize a new Git repository at a given path. If a repository already exists, the task is idempotent and will report no change.
options:
  repo:
    description: Path on the filesystem for the repository root (worktree for non-bare; repo dir for bare)
    type: path
    required: true
  bare:
    description: Create the repository as a bare repository
    type: boolean
    required: false
    default: false
'''

EXAMPLES = r'''
- name: Initialize a worktree repository
  git_init:
    repo: /home/example/projects/test_repo

- name: Initialize a bare repository
  git_init:
    repo: /srv/git/test_repo.git
    bare: true
'''

RETURN = r'''
changed:
  description: Whether any change was made
  type: bool
message:
  description: A human-readable message
  type: str
repo:
  description: The absolute path provided (normalized)
  type: str
bare:
  description: Whether the repository is bare
  type: bool
git_dir:
  description: Path to the Git directory (.git for non-bare, repo path for bare)
  type: str
'''

# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'path', "required": True},
    "bare": {"type": "bool", "required": False, "default": False},
}


def run_module():

    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
        "repo": '',
        "bare": False,
        "git_dir": None,
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    repo = module.params.get('repo')
    bare = module.params.get('bare')

    abs_repo = normalize_path(repo)
    result['repo'] = abs_repo
    result['bare'] = bare

    # In check mode, we still want to detect existence to return a helpful message
    existing_repo, git_dir = open_repository(abs_repo)
    if existing_repo is not None:
        result['git_dir'] = git_dir
        result['message'] = f"repository exists at {abs_repo}"
        result['changed'] = False
        module.exit_json(**result)

    # Not found
    if module.check_mode:
        result['message'] = f"would create repository at {abs_repo}"
        result['changed'] = False
        module.exit_json(**result)

    # we're now not in check mode and the repo doesn't exist, so we can create it
    try:
        pygit2.init_repository(abs_repo, bare=bare)
        # Re-open to populate git_dir consistently
        if bare:
            _, git_dir = open_repository(abs_repo)
        else:
            # For non-bare, .git will be inside the worktree
            _, git_dir = open_repository(abs_repo)
    except pygit2.GitError as e:
        module.fail_json(msg=f"failed to create repo at {abs_repo}", exception=str(e))

    result['git_dir'] = git_dir
    result['message'] = f"created repository at {abs_repo}"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
