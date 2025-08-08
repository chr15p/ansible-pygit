#
#### list files that have changed from HEAD (staged and unstaged)
#>>> t = repo.revparse_single("master").tree
#>>> for i in repo.diff(t):
#...     print(i.delta.old_file.path)
####
#
#### all files in repo
#index = repo.index
#
#index.read()
#>>> for entry in index:
#...     print(entry.path, entry.hex)
####
#
#### files changed in wrkdir but not staged
#index = repo.index
#for i in index.diff_to_workdir():
#...     print(i.delta.old_file.path)
#
####
#
#### files staged for commit
#t = repo.revparse_single("master").tree
#>>> for i in index.diff_to_tree(t):
#...     print(i.delta.old_file.path)
#...
####
#

import os
import pygit2

def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def open_repository(path: str) -> pygit2.Repository:
    try:
        return pygit2.Repository(path)
    except Exception:
        pass

    try:
        discovered = pygit2.discover_repository(path)
        if discovered:
            return pygit2.Repository(discovered)
    except Exception:
        pass

    raise pygit2.GitError(f"failed to get repo at {path}")


def relativize_path(repo_ref: pygit2.Repository, candidate_path: str) -> tuple[bool, str, str]:
    """Return a tuple (is_inside_repo, abs_path, rel_path).
    If candidate is relative, resolve against workdir first.
    """
    workdir = getattr(repo_ref, 'workdir', None)
    if not workdir:
        # For bare repos, staging files doesn't apply
        return False, candidate_path, candidate_path

    if os.path.isabs(candidate_path):
        abs_path = normalize_path(candidate_path)
    else:
        abs_path = normalize_path(os.path.join(workdir, candidate_path))

    is_inside = abs_path.startswith(workdir)
    rel_path = abs_path[len(workdir):].lstrip(os.sep) if is_inside else candidate_path
    return is_inside, abs_path, rel_path


def changed_files(repo, branch):
    """
    list files that have changed from HEAD (staged and unstaged)
    """
    changed = []
    t = repo.revparse_single(branch).tree
    for i in repo.diff(t):
        changed.append(i.delta.new_file.path)

    return changed

def all_repo_files(repo):
    """
    all files in repo
    """
    repo_files = []
    index = repo.index
    index.read()
    for entry in index:
        repo_files.append(entry.path)
    return repo_files


def unstaged_changes(repo):
    """
    files changed in workdir but not staged
    """
    index_files = []
    index = repo.index
    for i in index.diff_to_workdir():
        #print(i.delta.old_file.path)
        index_files.append(i.delta.new_file.path)
    return index_files


def staged_changes(repo, branch):
    """
    files staged for commit
    """
    staged_files = []
    index = repo.index
    t = repo.revparse_single(branch).tree
    for i in index.diff_to_tree(t):
        #print(i.delta.old_file.path)
        staged_files.append(i.delta.new_file.path)
    return staged_files


def get_credentials(username, pubkey, privkey, passphrase):

    if pubkey:
        return pygit2.Keypair(username, pubkey, privkey, passphrase)

    if username:
        return pygit2.Username(username)

    return None


def branch_exists(repo, branch_name):
    if repo.branches.get(branch_name):
        return True
    return False


def resolve_commit(repo, ref):
    try:
        commit, ref = repo.resolve_refish(ref)
    except KeyError:
        ## the ref doesn't exist
        return None
    return commit


def resolve_reference(repo, name):
    try:
        commit, ref = repo.resolve_refish(name)
    except KeyError:
        ## the ref doesn't exist
        return None
    return ref


def cannonicalise_name(repo, name):
    if name is None:
        if repo.head_is_unborn:
            name =  "HEAD"
        else:
            name = repo.head.name
    else:
        try:
            name = repo.lookup_reference_dwim(name).name
        except KeyError:
            name = f"refs/heads/{name}"

    return name


def get_status(repo):
    raw_status = repo.status()

    output_status={}
    for filepath, flags in raw_status.items():
        if flags == pygit2.enums.FileStatus.INDEX_NEW:
            output_status[filepath]="NEW"
        elif flags == pygit2.enums.FileStatus.INDEX_MODIFIED:
            output_status[filepath]="MODIFIED"
        elif flags == pygit2.enums.FileStatus.INDEX_DELETED:
            output_status[filepath]="DELETED"
        elif flags == pygit2.enums.FileStatus.INDEX_RENAMED:
            output_status[filepath]="RENAMED"
        elif flags == pygit2.enums.FileStatus.INDEX_TYPECHANGE:
            output_status[filepath]="TYPECHANGE"
        elif flags == pygit2.enums.FileStatus.IGNORED:
            output_status[filepath]="IGNORED"
        elif flags == pygit2.enums.FileStatus.CONFLICTED:
            output_status[filepath]="CONFLICTED"

    return output_status


def get_wt_changes(repo):
    raw_status = repo.status()

    output_status={}
    for filepath, flags in raw_status.items():
        if flags == pygit2.enums.FileStatus.WT_NEW:
            output_status[filepath]="NEW"
        elif flags == pygit2.enums.FileStatus.WT_MODIFIED:
            output_status[filepath]="MODIFIED"
        elif flags == pygit2.enums.FileStatus.WT_DELETED:
            output_status[filepath]="DELETED"
        elif flags == pygit2.enums.FileStatus.WT_TYPECHANGE:
            output_status[filepath]="TYPECHANGE"
        elif flags == pygit2.enums.FileStatus.WT_RENAMED:
            output_status[filepath]="WT_RENAMED:"
        elif flags == pygit2.enums.FileStatus.WT_UNREADABLE:
            output_status[filepath]="WT_UNREADABLE"

    return output_status
