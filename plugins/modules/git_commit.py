#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_commit
short description: add and commit one or more files
description: add a git commit
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  branch:
    description: the branch to commit to
    type: string
    required: false
    default: master
  msg:
    description: the message to add to the commit
    type: string
    required: false
    default: commited by ansible_pygit
  author:
    description: the name of the author for the commit
    type: string
    required: false
    default: ansible_pygit
  email:
    description: the email address for the author
    type: string
    required: false
    default: ansible_pygit@ansible.com 
'''

EXAMPLES = r'''
- name: git_commit
  git_commit:
    repo: /home/example/test_repo
    branch: master
    msg: "test commit from ansible_pygit"
    author: ansible_pygit
    email: "ansible_pygit@example.com"
'''

RETURN = r'''
commit:
  description: the commit id (sha) of the commit
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pygit_utils import *
import pygit2

# define available arguments/parameters a user can pass to the module
module_args = dict(
    repo = {"type": 'str', "required": True},
    branch = {"type": 'str', "required": False, "default": "master"},
    msg = {"type": 'str', "required": False, "default": "commited by ansible_pygit"},
    author = {"type": 'str', "required": False, "default": "ansible_pygit"},
    email = {"type": 'str', "required": False, "default": "ansible_pygit@ansible.com"},
)

def run_module():

    # seed the result dict in the object
    result = dict(
        changed = False,
        message = '',
        commit = '',
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
    branch = module.params.get('branch')
    msg = module.params.get('msg')
    author = module.params.get('author')
    email = module.params.get('email')

    try:
        repo_ref = pygit2.Repository(repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))


    ## if branch is not set try and get the currently checked out branch
    if branch == None and repo_ref.head_is_unborn:
        cannonical_name = "refs/heads/master"
        parents = []
    elif branch == None:
        cannonical_name = repo_ref.head.name
        parents = repo_ref.head.target
    elif repo_ref.head_is_unborn:
        cannonical_name = f"refs/heads/{branch}"
        parents = []
    else:
        try:
            branch_ref = repo_ref.lookup_reference_dwim(branch)
        except KeyError as e:
            module.fail_json(msg = f"can't resolve branch {branch}",
                             exception = str(e))
        cannonical_name = branch_ref.name
        parents = branch_ref.target

    status = get_status(repo_ref)
    if status == {}:
        result['message'] = f"no files staged for commit"
        module.exit_json(**result)
        
    
    #ref = resolve_reference(repo_ref, branch)
    #
    #if ref != None:
    #    ## we have a branch
    #    cannonical_name = ref.name
    #    parents = [ref.target]
    #elif ref == None \
    #        and list(repo_ref.branches) == [] \
    #        and branch in ["main", "master"]:
    #    ## there are no branchs (including master)
    #    ## so this is a brand new repo
    #    cannonical_name = f"refs/heads/{branch}"
    #    parents = []
    #else:
    #    module.fail_json(msg = f"can't resolve branch {branch}",
    #                     exception = f"does {branch} branch exist?")

    ## no files to commit
    #if staged_changes(repo_ref, branch) == []:
    #    result['message'] = f"no files staged for commit"
    #    module.exit_json(**result)
        

    ## if there are no branches at all then we will create it
    ## otherwise branch must exist
#    if branch_exists(repo_ref, branch):
#        branch_name = repo_ref.branches[branch].name
#        parents = [r.target]
#    elif list(repo_ref.branches) == []:
#        branch_name = "HEAD"
#        parents = []
#    else:
#        module.fail_json(msg = f"failed to get branch {branch}",
#                             exception = "branch does not exisst")

#    if list(repo_ref.branches) != []:
#        try:
#            branch_name = repo_ref.branches[branch].name
#        except KeyError as e:
#            module.fail_json(msg = f"failed to get branch {branch}",
#                             exception = str(e))
#
#        parents = [repo_ref.branches[branch].target]
#    else:
#        parents = []
#        branch_name = "HEAD"

    tree = repo_ref.index.write_tree()

    sig = pygit2.Signature(author, email)

    commit_ref = repo_ref.create_commit(cannonical_name, sig, sig, msg, tree, parents)

    result['commit'] = str(commit_ref)
    result['message'] = f"committed {commit_ref} to {branch}"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
