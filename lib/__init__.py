import argparse
import git  # FIXME: need >= 2.3, declare in requirements.txt
import lzma
import logging
import os.path as osp


# local
from .constants import *
dir()


def get_repo(name, base_dir=BASE_DIR, remote_tpl=REMOTE_TPL, origin=ORIGIN):
    # create base_dir if needed
    if not osp.isdir(base_dir):
        os.makedirs(base_dir)

    d = osp.join(base_dir, name)

    repo_url = remote_tpl.format(name)
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
    yield from repo.iter_commits(sl)


def full_version(o):
    if len(o.split('.')) != 3:
        raise argparse.ArgumentTypeError("Not a valid full version (x.y.z)")
    else:
        return o
