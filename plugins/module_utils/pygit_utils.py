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

import pygit2


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
        #print(entry.path, entry.hex)
        repo_files.append(i.delta.new_file.path)
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
    elif username:
        return pygit2.Username(username)
    else:
        return None


def branch_exists(repo, branch_name):
    if repo.branches.get(branch_name):
        return True
    return False


def resolve_commit(repo, ref):
    try:
        commit, ref = repo.resolve_refish(ref)
    except KeyError as e:
        ## the ref doesn't exist
        return None 
    return commit

def resolve_reference(repo, name):
    try:
        commit, ref = repo.resolve_refish(name)
    except KeyError as e:
        ## the ref doesn't exist
        return None 
    return ref
    

def cannonicalise_name(repo, name):
    if name == None:
        if repo.head_is_unborn:
            name = "refs/heads/master"
        else:
            name = repo.head.name
    else:
        try:
            name = repo.lookup_reference_dwim(name).name
        except KeyError as e:
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

#        elif flags == FileStatus.WT_NEW:
#            output_status[filepath]="
#        elif flags == FileStatus.WT_MODIFIED:
#            output_status[filepath]="
#        elif flags == FileStatus.WT_DELETED:
#            output_status[filepath]="
#        elif flags == FileStatus.WT_TYPECHANGE:
#            output_status[filepath]="
#        elif flags == FileStatus.WT_RENAMED:
#            output_status[filepath]="
#        elif flags == FileStatus.WT_UNREADABLE:
#            output_status[filepath]="
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
