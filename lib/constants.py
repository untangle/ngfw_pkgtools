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

NETBOOT_USER = 'buildbot'
NETBOOT_HOST = 'netboot-server.untangle.int'
NETBOOT_HTTP_DIR = 'untangle-images-buster'
NETBOOT_DIR = osp.join('/data', NETBOOT_HTTP_DIR)
