import re

# local
from .constants import *


def simple_version(version):
    if re.match(r'^\d+\.\d+$', version):
        return version


def full_version(version):
    if re.match(r'^\d+\.\d+\.\d+$', version):
        return version

