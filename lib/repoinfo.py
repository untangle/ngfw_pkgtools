import logging
import os.path as osp
import re
import yaml

from dataclasses import dataclass
from typing import List

from .constants import *


@dataclass
class VersionedResource:
    name: str
    resource_type: str
    change_on_release_branch: bool


@dataclass
class VersionedResourceFile(VersionedResource):
    """Versioned resource for a file"""
    path: str
    regex: str
    replacement: str

    def set_versioning_value(self, repo, locals_dict):
        file_name = self.path
        path = osp.join(repo.working_dir, file_name)
        value = self.replacement.format(**locals_dict)
        with open(path, 'r') as f:
            lines = f.readlines()

        with open(path, 'w') as f:
            for line in lines:
                line = re.sub(self.regex, self.replacement, line)
                f.write(line)

        msg = "{}: updating to {}".format(file_name, value)
        repo.index.add(file_name)
        repo.index.commit(msg)
        logging.info("on branch {}, {}".format(repo.head.reference, msg))


@dataclass
class VersionedResourceTag(VersionedResource):
    """Versioned resource for a tag"""
    value: str

    def set_versioning_value(self, repo, locals_dict):
        value = self.value.format(**locals_dict)        
        msg = "tagging {}".format(value)
        # FIXME: create empty commit first
        repo.create_tag(value, message=msg)
        # FIXME: push tags
        logging.info("on branch {}, {}".format(repo.head.reference, msg))


@dataclass
class RepositoryInfo:
    """Repository information in the context of a specific product"""
    name: str
    git_base_url: str
    versioned_resources: List[VersionedResource]
    git_url: str = ''
    default_branch: str = 'master'
    disable_branch_creation: bool = False
    disable_forward_merge: bool = False
    skip_versioning_entirely: bool = False
    private: bool = False

    def __post_init__(self):
        self.git_url = osp.join(self.git_base_url, self.name)


def read_source_info(yaml_file=YAML_REPOSITORY_INFO):
    with open(yaml_file) as f:
        try:
            y = yaml.load(f, Loader=yaml.FullLoader)
        except AttributeError:
            y = yaml.load(f, Loader=yaml.Loader)

    return y


def list_repositories(product, yaml_file=YAML_REPOSITORY_INFO):
    y = read_source_info(yaml_file)
    all_repositories = y['repositories']

    results = []
    for name, r in all_repositories.items():
        logging.debug("repoinfo looking at {} ({})".format(name, r))

        products = r['products']
        if product not in products:
            # this repository is not used by the target product
            continue

        p = products[product]
        if not p:
            p = {}  # or later .get will fail on None

        # 2 extra records to match RepositoryInfo
        r['name'] = name
        r['git_base_url'] = r.get('git_base_url', y['git_base_url'])
        # get those product-specific attributes
        r['default_branch'] = p.get('default_branch', 'master')
        r['disable_branch_creation'] = p.get('disable_branch_creation', False)
        r['skip_versioning_entirely'] = p.get('skip_versioning_entirely', False)
        r.pop('products')

        versioned_resources = []
        for vr in r.get('versioned_resources', []):
            if vr['resource_type'] == 'file':
                versioned_resources.append(VersionedResourceFile(**vr))
            elif vr['resource_type'] == 'tag':
                versioned_resources.append(VersionedResourceTag(**vr))
        r['versioned_resources'] = versioned_resources

        repo = RepositoryInfo(**r)
        results.append(repo)

    results.sort(reverse=True, key=lambda r: r.versioned_resources != [])
    logging.debug("repositories for product {}: {}".format(product, results))

    return results


def list_products(yaml_file=YAML_REPOSITORY_INFO):
    y = read_source_info(yaml_file)
    all_repositories = y['repositories']

    products = set()
    for r in all_repositories.values():
        for p in r['products']:
            products.add(p['name'])

    return products
