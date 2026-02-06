import os
import os.path as osp
import shutil
import sys


WORK_DIR = osp.join(os.getenv('HOME'), 'tmp', 'pkgtools-workdir')
# FIXME: separate cleanup() method, callable from other scripts
shutil.rmtree(WORK_DIR, ignore_errors=True)

YAML_REPOSITORY_INFO = osp.join(os.path.dirname(sys.argv[0]), 'repositories.yaml')

# Gerrit configuration
GERRIT_USER = os.getenv('GERRIT_USER', os.getenv('USER', 'buildbot'))

NETBOOT_USER = 'buildbot'
NETBOOT_HOST = 'package-server.untangle.int'
NETBOOT_BASE_DIR = '/data'
