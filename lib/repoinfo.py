import logging
import os.path as osp
import yaml

from dataclasses import dataclass
from typing import List

from .constants import *
from . import versioned_resource

@dataclass
class RepositoryInfo:
    """Repository information in the context of a specific product"""
    name: str
    git_base_url: str
    versioned_resources: List[versioned_resource.VersionedResource]
    git_url: str = ''
    default_branch: str = 'master'
    obsolete: bool = False
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


def list_repositories(product, yaml_file=YAML_REPOSITORY_INFO, include_obsolete=False):
    y = read_source_info(yaml_file)
    all_repositories = y['repositories']

    results = []
    for name, r in all_repositories.items():
        logging.debug("repoinfo looking at {} ({})".format(name, r))

        if r.get('obsolete', False) and not include_obsolete:
            continue

        products = r['products']
        if product not in products:
            # this repository is not used by the target product
            continue

        p = products[product]
        if not p:
            p = {}  # or later .get will fail on None

        # 2 extra records to match RepositoryInfo
        r['name'] = name
        
        # Determine git_base_url with priority:
        # 1. Repository-level git_source (e.g., 'gerrit' or 'github')
        # 2. Repository-level git_base_url
        # 3. Default git_base_url
        git_source = r.get('git_source')
        if git_source and 'git_sources' in y:
            git_base_url = y['git_sources'].get(git_source, y['default_git_base_url'])
            # Substitute {username} placeholder with GERRIT_USER
            r['git_base_url'] = git_base_url.format(username=GERRIT_USER)
        else:
            r['git_base_url'] = r.get('git_base_url', y['default_git_base_url'])
        
        # get those product-specific attributes
        r['default_branch'] = p.get('default_branch', 'master')
        r['disable_branch_creation'] = p.get('disable_branch_creation', False)
        r['skip_versioning_entirely'] = p.get('skip_versioning_entirely', False)
        
        # Remove keys that are not part of RepositoryInfo dataclass
        r.pop('products')
        r.pop('git_source', None)  # Remove git_source if it exists
        r.pop('git_sources', None)  # Remove git_sources if it exists

        versioned_resources = []
        for vr in r.get('versioned_resources', []):
            if vr['resource_type'] == 'file':
                versioned_resources.append(versioned_resource.VersionedResourceFile(**vr))
            elif vr['resource_type'] == 'tag':
                versioned_resources.append(versioned_resource.VersionedResourceTag(**vr))
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
