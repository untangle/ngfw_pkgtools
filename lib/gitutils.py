import git  # FIXME: need >= 2.3, declare in requirements.txt
import lzma
import logging
import os
import os.path as osp


# local
from .constants import WORK_DIR


def get_repo(repo_name, repo_url, base_dir=WORK_DIR, origin='origin', branch='master'):
    # create base_dir if needed
    if not osp.isdir(base_dir):
        os.makedirs(base_dir)

    d = osp.join(base_dir, repo_name)

    logging.info("get_repo for {}".format(repo_url))

    if osp.isdir(d):
        logging.info("using existing {} ".format(d))
        r = git.Repo(d)
        o = r.remote(origin)
        o.fetch()
        r.heads[branch].checkout()
    else:
        logging.info("cloning from remote into {} on branch {}".format(d, branch))
        r = git.Repo.clone_from(repo_url, d, branch=branch)
        o = r.remote(origin)

    return r, o


def create_commit(repo, files, msg):
    for f in files:
        repo.index.add(f)

    repo.index.commit(msg)
    logging.info("on branch {}, commit files {} with message '{}'".format(repo.head.reference, list(files), msg))


def create_tag(repo, tag_name, msg):
    repo.create_tag(tag_name, message=msg)
    logging.info("on branch {}, tag {} with message '{}'".format(repo.head.reference, tag_name, msg))


def push(origin, refspecs, simulate=True):
    if not simulate:
        logging.info("pushing refspecs {}".format(refspecs))
        for refspec in refspecs:
            origin.push(refspec)
    else:
        logging.info("would push refspecs {}".format(refspecs))


def list_commits_between(repo, old, new):
    sl = "{}...{}".format(old, new)
    logging.info("running git log {}".format(sl))
    try:
        yield from repo.iter_commits(sl)
    except git.exc.GitCommandError as e:
        if e.stderr.find('bad revision') >= 0:
            logging.warning("... could not diff revisions")
            return
        else:
            raise


def archive_repo_lz(repo, dst, treeish='master'):
    logging.info("creating archive {} from {}".format(dst, treeish))
    repo.archive(lzma.open(dst, 'w'), treeish=treeish)
