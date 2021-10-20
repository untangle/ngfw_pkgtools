import yaml

from dataclasses import dataclass

from .constants import *


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
    with open(YAML_REPOSITORY_INFO) as f:
        try:
            y = yaml.load(f, Loader=yaml.FullLoader)
        except AttributeError:
            y = yaml.load(f, Loader=yaml.Loader)

    return y


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
