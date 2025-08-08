#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# MIT License (see LICENSE)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_push
short description: tag a git commit
description: tag a git commit
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  remote:
    description: the remote to push to
    type: string
    required: false
    default: origin
  branch:
    description: a list of branches to push to the remote
    type: list
    default: origin
    required: false
    aliases: head, heads, branches
  tags:
    description: a list of tags to push to the remote
    type: list
    default: origin
    required: false
    aliases: tag
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
- git_push:
    repo: /home/example/test_repo
    tags: 
      - test_tag2
      - test_tag4
    username: git
    pubkey: /home/example/.ssh/id_rsa.pub
    privkey: /home/example/.ssh/id_rsa

- git_push:
    repo: /home/example/test_repo
    branch: 
      - master
      - test
    username: git
    pubkey: /home/example/.ssh/id_rsa.pub
    privkey: /home/example/.ssh/id_rsa
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
    branch = {"type": 'list', "required": False, "aliases": ['head', 'heads', 'branches']},
    tags = {"type": 'list', "required": False, "aliases": ['tag']},
    remote = {"type": 'str', "required": False, 'default': 'origin'},
    username = {"type": 'str', "required": False, 'default': 'git'},
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
    remote = module.params.get('remote')
    branch = module.params.get('branch', [])
    tags = module.params.get('tags', [])
    username = module.params.get('username')
    pubkey = module.params.get('pubkey')
    privkey = module.params.get('privkey')
    passphrase = module.params.get('passphrase')

    try:
        repo_ref = pygit2.Repository( repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))

    try:
        remote_ref = repo_ref.remotes[remote]
    except KeyError as e:
        module.fail_json(msg = f"failed to get remote {remote}",
                                exception = str(e))


    credentials = get_credentials(username, pubkey, privkey, passphrase)
    #credentials = pygit2.Keypair(username, pubkey, privkey, passphrase)

    callbacks=pygit2.RemoteCallbacks(credentials=credentials)

    refs = []
    if branch != None:
        for b in branch:
            refs.append(cannonicalise_name(repo_ref, b))

    if tags != None:
        for t in tags:
            refs.append(cannonicalise_name(repo_ref, t))
            #refs.append(f"refs/tags/{t}")

    if refs == []:
        module.fail_json(msg = f"either branch or tags must be defined")

    try:
        _ = remote_ref.push(refs, callbacks=callbacks)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to push refs {refs} to {remote}",  exception = str(e))

    result['message'] = f"pushed to {branch} at {remote}"

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
