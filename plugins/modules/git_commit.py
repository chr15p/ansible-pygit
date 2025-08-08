#!/usr/bin/python

# Copyright: (c) 2025, Chris Procter <chris@chrisprocter.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.pygit_utils import (
    get_status,
    normalize_path,
    open_repository,
    cannonicalise_name,
    resolve_reference,
)
import pygit2
DOCUMENTATION = r'''
---
module: git_commit
short_description: Create a Git commit from the current index
description: Creates a commit using files currently staged in the index. If no files are staged, the task is idempotent and reports no change.
options:
  repo:
    description: Path to the Git repository worktree
    type: path
    required: true
  branch:
    description: Branch to commit to. If omitted, uses the current HEAD, or creates the default branch for an unborn repo.
    type: string
    required: false
    default: null
  msg:
    description: Commit message
    type: string
    required: false
    default: commited by ansible_pygit
  author:
    description: Author name
    type: string
    required: false
    default: ansible_pygit
  email:
    description: Author email
    type: string
    required: false
    default: ansible_pygit@ansible.com
'''

EXAMPLES = r'''
- name: Commit staged changes
  git_commit:
    repo: /home/example/test_repo
    msg: "test commit from ansible_pygit"
    author: ansible_pygit
    email: ansible_pygit@example.com
'''

RETURN = r'''
commit:
  description: the commit id (sha) of the created commit
  type: str
'''

# define available arguments/parameters a user can pass to the module
module_args = {
    "repo": {"type": 'path', "required": True},
    "branch": {"type": 'str', "required": False, "default": None},
    "msg": {"type": 'str', "required": False, "default": "commited by ansible_pygit"},
    "author": {"type": 'str', "required": False, "default": "ansible_pygit"},
    "email": {"type": 'str', "required": False, "default": "ansible_pygit@ansible.com"},
}

def _open_repo(repo_param):
    repo_open = open_repository(normalize_path(repo_param))
    # Support both (repo, git_dir) tuple and bare repo object returns
    if isinstance(repo_open, tuple):
        repo_ref, _git_dir = repo_open
    else:
        repo_ref = repo_open
    if repo_ref is None:
        raise pygit2.GitError(f"failed to get repo at {repo_param}")
    return repo_ref

def _determine_ref_and_parents(repo_ref: pygit2.Repository, branch: str | None) -> tuple[str, list]:
    canonical_name = cannonicalise_name(repo_ref, branch)
    # Determine parents
    if repo_ref.head_is_unborn:
        parents = []
    else:
        if branch is None:
            parents = [repo_ref.head.target]
        else:
            ref = resolve_reference(repo_ref, branch)
            if ref is None:
                # If there are no branches yet, allow creating initial commit
                if not list(repo_ref.branches):
                    parents = []
                else:
                    raise KeyError(f"can't resolve branch {branch}")
            else:
                parents = [ref.target]
    return canonical_name, parents

def run_module():

    # seed the result dict in the object
    result = {
        "changed": False,
        "message": '',
        "commit": '',
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    repo = module.params.get('repo')
    branch = module.params.get('branch')
    msg = module.params.get('msg')
    author = module.params.get('author')
    email = module.params.get('email')

    try:
        repo_ref = open_repository(normalize_path(repo))
    except pygit2.GitError as e:
        module.fail_json(msg=f"failed to get repo at {repo}", exception=str(e))

    status = get_status(repo_ref)
    if status == {}:
        result['message'] = "no files staged for commit"
        module.exit_json(**result)

    canonical_name, parents = None, []
    try:
        canonical_name, parents = _determine_ref_and_parents(repo_ref, branch)
    except KeyError as e:
        module.fail_json(msg=str(e), exception=str(e))

    tree = repo_ref.index.write_tree()
    sig = pygit2.Signature(author, email)

    if module.check_mode:
        result['message'] = f"would create commit on {canonical_name}"
        module.exit_json(**result)

    commit_ref = repo_ref.create_commit(canonical_name, sig, sig, msg, tree, parents)

    result['commit'] = str(commit_ref)
    result['message'] = f"committed {commit_ref} to {branch if branch else canonical_name}"
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
