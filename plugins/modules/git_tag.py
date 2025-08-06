#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: git_tag
short description: tag a git commit
description: tag a git commit
options:
  repo:
    description: Path on the filesystem to find the git repo
    type: string
    required: true
  action:
    description: add or delete the tag
    type: string
    required: false
    choices: add, delete
    default: add
  ref:
    description: the ref-ish object the tag points to
    type: string
    required: false
    aliases: branch
  tag:
    description: the tag to point to
    type: string
    required: false
  msg:
    description: the message to add to the commit
    type: string
    required: false
  author:
    description: the name of the author for the commit
    type: string
    required: false
  email:
    description: the email address for the author
    type: string
    required: false
'''

EXAMPLES = r'''
- git_tag:
    repo: /home/chrisp/projects/test_repo
    ref: master
    tag: "test_tag2"
    msg: "a test tag"
    author: 'chrisp'
    email: 'cprocter@redhat.com'
'''

RETURN = r'''
None
'''

from ansible.module_utils.basic import AnsibleModule
import pygit2

def git_tag_commit_add(repo_ref, ref, tag, msg, author, email):
    commit, reference = repo_ref.resolve_refish( ref )

    sig = pygit2.Signature(author, email)
    #tag_id = repo_ref.create_tag( tag, reference.target, reference.type, sig,  msg)
    tag_id = repo_ref.create_tag( tag, commit.oid, commit.type, sig,  msg)
    return tag_id


def git_tag_commit_delete(repo_ref, tag):
    _, reference = repo_ref.resolve_refish( tag )

    reference.delete()


# define available arguments/parameters a user can pass to the module
module_args = dict(
    repo = {"type": 'str', "required": True},
    action = {"type": 'str', "required": False, "choices": ['add', 'delete'], "default": 'add'},
    ref = {"type": 'str', "required": False, "aliases": ['branch']},
    tag = {"type": 'str', "required": False},
    msg = {"type": 'str', "required": False},
    author = {"type": 'str', "required": False},
    email = {"type": 'str', "required": False},
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
    action = module.params.get('action')
    ref = module.params.get('ref')
    tag = module.params.get('tag')
    msg = module.params.get('msg')
    author = module.params.get('author')
    email = module.params.get('email')
#    if not msg:
#        msg = module.params['tag']

    if action == 'add':
        if ref is None or author is None or email is None:
            ansible_module.fail_json(msg="When adding ref, author, and email are required")

    try:
        repo_ref = pygit2.Repository( repo)
    except pygit2.GitError as e:
        module.fail_json(msg = f"failed to get repo at {repo}",
                         exception = str(e))
        

    result['tag'] = tag
    try:
        _, _ = repo_ref.resolve_refish( tag)
             
    except KeyError:
        tag_exists = False
    else:
        tag_exists = True

    
    if tag_exists == False and action != 'delete':
        try:
            _, _ = repo_ref.resolve_refish(ref)
        except KeyError as e:
            ## the ref doesn't exist
             module.fail_json(msg = f"failed to get {ref}",
                             exception = str(e))

        ## tag doesn't exist and its to be added
        try:
            _ = git_tag_commit_add( repo_ref,
                    ref,
                    tag,
                    msg,
                    author,
                    email)
        except Exception as e:
             module.fail_json(msg = f"failed to add commit {ref}",
                             exception = str(e))

        output_msg = f"tag { tag} applied to ref { ref}"
        result['changed'] = True

    elif tag_exists == True and action != 'delete':
        ## tag exist and its to be added
        output_msg = f"tag { tag} already exists"
        result['changed'] = False

    elif tag_exists == True and action == 'delete':
        ## tag exist and its to be deleted
        _ = git_tag_commit_delete(repo_ref, tag)


        output_msg = f"tag { tag} deleted"
    else:
        ## tag doesn't exist and its to be deleted
        output_msg = f"tag { tag} doesn't exist"
        result['changed'] = False


    result['message'] = output_msg

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
