#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_init
short description: 
description: 
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  bare:
    description: repo should be created as a bare repo
    type: boolean
    required: false
    default: false
'''

EXAMPLES = r'''
- name: git_init
  git_init:
    repo: /home/example/projects/test_repo
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
    "bare": {"type": "bool", "required": False, "default": False},
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
    bare = module.params.get('bare')

    #if repo[-4:] != ".git":
    #    repo = repo +"/.git"

    if pygit2.discover_repository(repo):
        result['message'] = f"repository exists at { repo }"
        result['changed'] = False

        module.exit_json(**result)
    
    try:
        pygit2.init_repository(repo, bare=bare)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to create repo at {repo}",
                         exception = str(e))

    result['message'] = f"created repository at { repo }"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
