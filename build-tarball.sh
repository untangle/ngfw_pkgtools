#!/bin/dash

usage() {
    echo "USAGE $0 <type> [<branch>] [<revision>]"
    echo "\tThis will create a tarball of the current trunk"
    echo "\t<type> is the type of the release,"
    echo "\t\tthis is typically either development, beta, or release." 
    echo "\t\tThe version string and, svn revision are automatically appended."
    echo "\t<branch> is the branch to use, do not specify 'svn://chef/'."
    echo "\t\t the file svn://chef/\${branch}/version/resources/VERSION should exist"
    echo "\t<revision> Subversion revision number to use."
    exit 2
}

TARBALL_TYPE=$1

BRANCH=$2
## Default to the normal branch if it isn't specified
BRANCH=${BRANCH:-work}
BRANCH=${BRANCH:+svn://chef/${BRANCH}}

if [ $# -gt 3 ] || [ -z "${TARBALL_TYPE}" ]; then usage ; fi

## Get the version string
RELEASE_VERSION=`svn cat ${BRANCH}/version/resources/VERSION`

SUBVERSION_REVISION=$3

if [ -z "${SUBVERSION_REVISION}" ]; then
    ## Get the subversion release
    SUBVERSION_REVISION=`svn info ${BRANCH} | awk '/^Last Changed Rev:/ { print $4}'`
fi

if [ -z "${SUBVERSION_REVISION}" ] || [ -z "${RELEASE_VERSION}" ]; then
    echo "ERROR: Unable to determine subversion revision or version number"
    echo "\tAttempting to use the branch ${BRANCH}"
    usage
fi

EXPORT_DIRECTORY=`mktemp -d`
ARCHIVE=`date +"untangle-${TARBALL_TYPE}-${RELEASE_VERSION}-%Y%m%dr${SUBVERSION_REVISION}"`

## Export the tree into the export directory
echo "[svn] export -r ${SUBVERSION_REVISION} ${BRANCH} ${EXPORT_DIRECTORY}/${ARCHIVE}"
svn export -r ${SUBVERSION_REVISION} ${BRANCH} ${EXPORT_DIRECTORY}/${ARCHIVE}

if [ "${BRANCH}x" !=  "svn://chef/work" ]; then
    echo "${BRANCH}@${SUBVERSION_REVISION}" > ${EXPORT_DIRECTORY}/${ARCHIVE}/.untangle_branch
fi

cat <<EOF | fakeroot
echo "[chown] -R root:root ${EXPORT_DIRECTORY}/${ARCHIVE}"
chown -R root:root ${EXPORT_DIRECTORY}/${ARCHIVE}
echo "[tar] -C ${EXPORT_DIRECTORY} -czf ${ARCHIVE}.tar.gz ${ARCHIVE}"
tar -C ${EXPORT_DIRECTORY} -czf ${ARCHIVE}.tar.gz ${ARCHIVE}
EOF

echo "[rm] ${EXPORT_DIRECTORY}"
rm -rf ${EXPORT_DIRECTORY}

echo "[fin] archive is ready in ${ARCHIVE}.tar.gz"


