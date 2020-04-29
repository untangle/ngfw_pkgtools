import os
import os.path as osp

PROJECT = 'NGFW'
BASE_DIR = osp.join(os.getenv('HOME'), 'tmp')

ORIGIN = 'origin'
BRANCH_TPL = '{}/release-{{}}'.format(ORIGIN)

REMOTE_TPL = 'git@github.com:untangle/{}.git'
PREFIXED_REPOSITORIES = ['src', 'pkgs', 'hades-pkgs', 'kernels', 'imgtools']
REGULAR_REPOSITORIES = ['debian-cloud-images']
REPOSITORIES = ['{}_{}'.format(PROJECT.lower(), e) for e in PREFIXED_REPOSITORIES] + REGULAR_REPOSITORIES
