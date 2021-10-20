import os
import os.path as osp
import shutil

WORK_DIR = osp.join(os.getenv('HOME'), 'tmp', 'pkgtools-workdir')
# FIXME: separate cleanup() method, callable from other scripts
shutil.rmtree(WORK_DIR, ignore_errors=True)

YAML_REPOSITORY_INFO = 'repositories.yaml'

NETBOOT_USER = 'buildbot'
NETBOOT_HOST = 'netboot-server.untangle.int'
NETBOOT_HTTP_DIR = 'untangle-images-buster'
NETBOOT_DIR = osp.join('/data', NETBOOT_HTTP_DIR)
