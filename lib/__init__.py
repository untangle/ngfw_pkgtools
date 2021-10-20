import re

# local
from .constants import *


def simple_version(version):
    if re.match(r'^\d+\.\d+$', version):
        return version
    else:
        raise ValueError("not a valid simple version (x.y)")


def full_version(version):
    if re.match(r'^\d+\.\d+\.\d+$', version):
        return version
    else:
        raise ValueError("not a valid full version (x.y.z)")
