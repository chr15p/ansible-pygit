#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# MIT License (see LICENSE)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_restore
short description: 
description: 
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  files:
    description: the list of files to restore
    type: list
    required: true
  branch:
    description: the branch to restore the files from
    type: string
    required: true
  option:
    description: if set to staged only restore the staging area,
                 otherwise restore the workdir from branch as well
    type: string
    default: staged 
    required: false
'''

EXAMPLES = r'''
- name: git_restore
  git_restore:
    repo: /home/example/projects/test_repo
    branch: master
    option: workdir
    files:
     - test_file
'''

RETURN = r'''
restored_files:
    description: files successfully restored in the working directory
    type: list
unstaged_files:
    description: files successfully restored in the staging area
    type: list
'''

import os
from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import *

# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'str', "required": True},
    "files": {"type": "list", "required": True},
    "branch": {"type": "str", "required": True},
    "option": {"type": "str", "required": False, "default": "staged"},
}

def run_module():

    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
        "restored_files": [],
        "unstaged_files": [],
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
    files = module.params.get('files')
    branch = module.params.get('branch')
    option = module.params.get('option')

    try:
        repo_ref = pygit2.Repository(repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))

    restored_files = []
    unstaged_files = []
    index = repo_ref.index

    branch_oid = repo_ref.revparse_single(branch) # Get object from db

    staged_files = staged_changes(repo_ref, branch) 
    unstaged_files = unstaged_changes(repo_ref)

    for f in files:
        if option not in [ "staged", "cached"] \
            and (f in staged_files or f in unstaged_files):

            try:
                os.remove(f"{repo}/{f}")
            except FileNotFoundError:
                pass

            restored_files.append(f)            
            repo_ref.checkout_tree(branch_oid, paths=[f])

        if f in staged_files:
            index.remove(f)
            unstaged_files.append(f)

            obj = branch_oid.tree[f] # Get object from db

            ### restore the working tree
            index.add(pygit2.IndexEntry(f, obj.id, obj.filemode)) # Add to index


    index.write()


    if not unstaged_files and not restored_files:
        result['message'] = "no files restored"
    else:
        result['restored_files'] = restored_files
        result['unstaged_files'] = unstaged_files
        result['message'] = f"restored {','.join(restored_files+unstaged_files)}"
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
