import os.path as osp
import re

from dataclasses import dataclass

from . import gitutils


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
                line = re.sub(self.regex, value, line)
                f.write(line)

        msg = "{}: updating to {}".format(file_name, value)
        gitutils.create_commit(repo, (file_name,), msg)

        refspec = "{}:{}".format(repo.head.reference, repo.head.reference)
        return (refspec,)


@dataclass
class VersionedResourceTag(VersionedResource):
    """Versioned resource for a tag"""
    value: str

    def set_versioning_value(self, repo, locals_dict):
        tag_name = self.value.format(**locals_dict)
        msg = "Release branching: new version is {}".format(tag_name)

        # create empty commit first, to make sure the upcoming tag
        # does not also apply to the release branch
        gitutils.create_commit(repo, (), msg)

        gitutils.create_tag(repo, tag_name, msg)

        refspecs = ("{}:{}".format(repo.head.reference, repo.head.reference),
                    "{}:{}".format(tag_name, tag_name))
        return refspecs

