#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_checkout
short description: 
description: 
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  branch:
    description: the branch to checkout
    type: string
    required: true
  files:
    description: only checkout specific files and do not set HEAD to branch
    type: list
    required: false
  force:
    description: force checkout, overwriting any changes in the workdir
    type: boolean
    required: false
    default: false
'''

EXAMPLES = r'''
- name: git_restore
  git_restore:
    repo: /home/example/projects/test_repo
    branch: master
'''

RETURN = r'''
None
'''

import os
from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import *

# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'str', "required": True},
    "branch": {"type": "str", "required": True},
    "files": {"type": "list", "required": False},
    "force": {"type": "bool", "required": False, "default": False},
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

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    repo = module.params.get('repo')
    branch = module.params.get('branch')
    files = module.params.get('files')
    force = module.params.get('force')

    try:
        repo_ref = pygit2.Repository(repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))

    ref = resolve_reference(repo_ref, branch)
    if ref == None:
        module.fail_json(msg = f"can't resolve branch {branch}",
                         exception = f"does {branch} branch exist?")

    if force:
        strategy = pygit2.enums.CheckoutStrategy.RECREATE_MISSING | pygit2.enums.CheckoutStrategy.FORCE
    else:
        strategy = pygit2.enums.CheckoutStrategy.RECREATE_MISSING | pygit2.enums.CheckoutStrategy.SAFE
    
    if files == None and repo_ref.branches[branch].is_checked_out():
        result['message'] = f"{ branch } already checked out"
        result['changed'] = False

        module.exit_json(**result)

    elif files == None:
        repo_ref.checkout(refname=ref, strategy=strategy)
        result['message'] = f"checked out { branch }"
        result['changed'] = True
            
    else:
        #repo_one.checkout('refs/heads/master', paths=files, strategy=strategy)
        #repo_one.checkout(refname=ref, paths=files, strategy=strategy)
        repo_ref.checkout(refname=ref, paths=files, strategy=strategy)
        result['message'] = f"checked out files: { ",".join(files) }"
        result['changed'] = True
         
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
