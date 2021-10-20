import git  # FIXME: need >= 2.3, declare in requirements.txt
import lzma
import logging
import os.path as osp
import re
import yaml

from dataclasses import dataclass
from typing import ClassVar, List

# local
from .constants import *


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


def simple_version(version):
    if re.match(r'^\d+\.\d+$', version):
        return version


def full_version(version):
    if re.match(r'^\d+\.\d+\.\d+$', version):
        return version


def archive_repo_lz(repo, dst, treeish='master'):
    logging.info("creating archive {} from {}".format(dst, treeish))
    repo.archive(lzma.open(dst, 'w'), treeish=treeish)


@dataclass
class RepositoryInfo:
    """Repository information in the context of a specific product """
    name: str
    git_base_url: str
    git_url: str = ''
    default_branch: str = 'master'
    contains_versioning_info: bool = False
    disable_branch_creation: bool = False
    disable_forward_merge: bool = False

    def __post_init__(self):
        self.git_url = osp.join(self.git_base_url, self.name)


def read_source_info():
    return yaml.load(open(YAML_SOURCE_INFO), Loader=yaml.FullLoader)


def list_repositories(product):
    y = read_source_info()
    all_repositories = y['repositories']

    results = []
    for r in all_repositories:
        for p in r['products']:
            if p['name'] == product:
                r['git_base_url'] = r.get('git_base_url', y['git_base_url'])
                r['default_branch'] = p.get('default_branch', 'master')
                r.pop('products')

                repo = RepositoryInfo(**r)
                results.append(repo)

    results.sort(reverse=True, key=lambda r: r.contains_versioning_info)
    return results


def list_products():
    y = read_source_info()
    all_repositories = y['repositories']

    products = set()
    for r in all_repositories:
        for p in r['products']:
            products.add(p['name'])

    return products
