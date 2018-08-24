#! /bin/bash

set -e

usage() {
  echo "Usage: $0 [-s] [-w] -r <repository> -v <version>"
  echo "-s : simulate"
  echo "-w : wipe out target before sync'ing"
  echo "-r : repository to use"
  echo "-v : version (needs to be a full x.y.z)"
  exit 1
}

while getopts "wshr:v:" opt ; do
  case "$opt" in
    s) simulate=1 ;;
    w) WIPE_OUT_TARGET=1 ;;
    r) REPOSITORY=$OPTARG ;;
    v) VERSION=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 0 ] ; then
  usage
fi

[ -z "$REPOSITORY" -o -z "$VERSION" ] && usage && exit 1

#########
# MAIN

# include common variables
. $(dirname $0)/release-constants.sh
CHANGELOG_FILE="sync.txt"

copyRemotePkgtools

if [ -z "$simulate" ] ; then
  # wipe out target distribution first
  [ -n "$WIPE_OUT_TARGET" ] && remoteCommand ./remove-packages.sh -r ${REPOSITORY} -d ${VERSION}

  repreproRemote --noskipold update ${VERSION}

  repreproRemote export ${VERSION}
else
  repreproRemote "checkupdate $VERSION 2>&1 | grep upgraded | sort -u"
fi

# remove remote pkgtools
removeRemotePkgtools

# generate changelog
diffCommand="python3 ${PKGTOOLS}/changelog.py --log-level info --version $VERSION --tag-type sync"
if [ -z "$simulate" ] ; then
  diffCommand="$diffCommand --create-tags"
fi
$diffCommand >| $CHANGELOG_FILE
cat $CHANGELOG_FILE
