#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# MIT License (see LICENSE)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_clone
short description: clone a repo
description: clone a repo to a location on the filesystem
options:
  upstream:
    description: url of repo to clone
    type: string
    required: true
  repo:
    description: Path on the filesystem to clone to
    type: string
    required: true
  bare:
    description: branch to checkout
    type: boolean
    required: false
    default: false
  branch:
    description: clone o a bare repo
    type: string
    required: false
    default: master
  username:
    description: the username for the remote repo (if required)
    type: string
    default: git
    required: false
  pubkey:
    description: the path to a public key file for push via ssh
    type: string
    required: false
  privkey:
    description: the path to the private key for push via ssh
    type: string
    required: false
  passphrase:
    description: the passphrase to access the keypair (if required)
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

# define available arguments/parameters a user can pass to the module
module_args = dict(
    repo = {"type": 'str', "required": True},
    upstream = {"type": 'str', "required": True},
    bare = {"type": 'bool', "required": False, "default": False},
    branch = {"type": 'str', "required": False, "default": "master"},
    username = {"type": 'str', "required": False},
    pubkey = {"type": 'str', "required": False},
    privkey = {"type": 'str', "required": False},
    passphrase = {"type": 'str', "required": False, "no_log": True},
)

def run_module():

    # seed the result dict in the object
    result = dict(
        changed = False,
        message = '',
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
    upstream = module.params.get('upstream')
    bare = module.params.get('bare')
    branch = module.params.get('branch')
    username = module.params.get('username')
    pubkey = module.params.get('pubkey')
    privkey = module.params.get('privkey')
    passphrase = module.params.get('passphrase')

    if pygit2.discover_repository(repo):
        result['message'] = f"repository exists at { repo }"
        result['changed'] = False

        module.exit_json(**result)


    credentials = get_credentials(username, pubkey, privkey, passphrase)

    callbacks = pygit2.RemoteCallbacks(credentials=credentials)

    if upstream[0] == '/':
        upstream = f"file://{upstream}"

    try:
        pygit2.clone_repository(upstream, repo, checkout_branch=branch,
                                callbacks=callbacks, bare=bare)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed clone { upstream } to {repo}",  exception = str(e))
    except KeyError as e:
        module.fail_json(msg = f"branch { branch} does not exist in { upstream }",  exception = str(e))

    result['changed'] = True
    result['message'] = f"cloned {upstream} at {repo}"

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
