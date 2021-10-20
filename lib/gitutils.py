import git  # FIXME: need >= 2.3, declare in requirements.txt
import lzma
import logging
import os
import os.path as osp


# local
from .constants import WORK_DIR


def get_repo(repo_name, repo_url, base_dir=WORK_DIR, origin='origin'):
    # create base_dir if needed
    if not osp.isdir(base_dir):
        os.makedirs(base_dir)

    d = osp.join(base_dir, repo_name)

    logging.info("looking at {}".format(repo_url))

    if osp.isdir(d):
        logging.info("using existing {} ".format(d))
        r = git.Repo(d)
        o = r.remote(origin)
        o.fetch()
    else:
        logging.info("cloning from remote into {} ".format(d))
        r = git.Repo.clone_from(repo_url, d)
        o = r.remote(origin)

    return r, o


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
