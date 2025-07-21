#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_branch
short description: 
description:
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  action:
    description: add or delete the branch
    type: string
    required: false
    choices: add, delete
    default: add
  parent:
    description: branch to fork from 
    type: string
    required: false
    default: master
    aliases: branch
  name:
    description: name of the branch to create or delete
    type: string
    required: false 
'''

EXAMPLES = r'''
'''

RETURN = r'''
None
'''

from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import *

module_args = dict(
    repo = {"type": 'str', "required": True},
    action = {"type": 'str', "required": False, "choices": ['add', 'delete'], "default": 'add'},
    parent = {"type": 'str', "required": False, "default": "master"},
    name = {"type": 'str', "required": False, "aliases": ['branch']},
)

def run_module():
    # define available arguments/parameters a user can pass to the module
#    module_args = dict(
#        repo = {"type": 'str', "required": True},
#        action = {"type": 'str', "required": False, "choices": ['add', 'delete'], "default": 'add'},
#        parent = {"type": 'str', "required": False, "aliases": ['branch']},
#        name = {"type": 'str', "required": False},
#    )

    # seed the result dict in the object
    result = dict(
        changed = False,
        message = '',
        tag = '',
    )

    module = AnsibleModule(
        argument_spec = module_args,
        supports_check_mode = True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    repo = module.params.get('repo')
    action = module.params.get('action')
    parent = module.params.get('parent')
    name = module.params.get('name')

    if action == 'delete':
        if name is None:
            AnsibleModule.fail_json(msg="Name is required when deleting a branch")

    try:
        repo_ref = pygit2.Repository( repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))
        

    # read index
    repo_ref.index.read()

    # or create from another branch
    branch = repo_ref.lookup_branch(name)

    if action == "delete" and branch == None:
        output_msg = f"branch { name } does not exist"
        result['changed'] = False
    
    elif action == "delete" and branch != None:
        branch.delete()
        output_msg = f"branch { name } deleted"
        result['changed'] = True

    elif action == "add" and branch == None:
        parent_commit = resolve_commit(repo_ref, parent)
        if parent_commit == None:
            module.fail_json(msg=f"{ parent } not found in {repo}")
            
        #parent_branch = repo_ref.lookup_branch(parent)
        #branch = repo_ref.create_branch(name, parent_branch.peel())
        new_branch = repo_ref.create_branch(name, parent_commit)
        output_msg = f"branch { name } created"
        result['changed'] = True

    elif action == "add" and branch != None:
        output_msg = f"branch { name } already exists"
        result['changed'] = False

    result['message'] = output_msg

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
