#!/usr/bin/python

# Copyright: (c) 2024, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_add
short description: add and commit one or more files
description: add a git commit
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  files:
    description: the files to add
    type: list
    required: true
'''

EXAMPLES = r'''
 - name: git_add
   git_add:
     repo: /home/example/projects/test_repo
     files:
     - test_file1
     - test_file2
'''

RETURN = r'''
added_files:
  description: The list of files staged by this task
  type: list
status:
  description: A dict with the files currently staged for commit as keys
               and their statuses as the values
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
import pygit2
from ansible.module_utils.pygit_utils import *

# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'str', "required": True},
    "files": {"type": "list", "required": True},
}

def run_module():

    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
        "added_files": [],
        "status": [],
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

    try:
        repo_ref = pygit2.Repository(repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))

    #commit = resolve_commit(repo_ref, branch)

    index = repo_ref.index

    wt = get_wt_changes(repo_ref)

    added_files = []

    for f in files:
        rel_file = f.removeprefix(repo_ref.workdir)
        if wt.get(rel_file):
            index.add(rel_file)
            added_files.append(rel_file)

    index.write()

    result['status'] = get_status(repo_ref)

    if not added_files:
        result['message'] = "no new files added for commit"
    else:
        result['added_files'] = added_files
        result['message'] = f"staged {','.join(added_files)} for commit"
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
