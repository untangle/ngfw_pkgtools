#! /bin/bash

set -e

usage() {
  echo "Usage: $0 [-s] [-w] -r <repository> -d <target_distribution>"
  echo "-s : simulate"
  echo "-w : wipe out target before sync'ing"
  echo "-r : repository to use"
  echo "-d : target distribution (needs to be a full <product>-x.y.z)"
  exit 1
}

while getopts "wshr:d:" opt ; do
  case "$opt" in
    s) simulate=1 ;;
    w) WIPE_OUT_TARGET=1 ;;
    r) REPOSITORY=$OPTARG ;;
    d) TARGET_DISTRIBUTION=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 0 ] ; then
  usage
fi

[ -z "$REPOSITORY" -o -z "$TARGET_DISTRIBUTION" ] && usage && exit 1

#########
# MAIN

# include common variables
. $(dirname $0)/lib/constants.sh
CHANGELOG_FILE="sync.txt"

# start with a clean changelog, as the one from the previous run might
# still be present
echo >| $CHANGELOG_FILE

copyRemotePkgtools

if [ -z "$simulate" ] ; then
  # wipe out target distribution first
  [ -n "$WIPE_OUT_TARGET" ] && remoteCommand ./remove-packages.sh -r ${REPOSITORY} -d ${TARGET_DISTRIBUTION}

  repreproRemote --noskipold update ${TARGET_DISTRIBUTION}

  repreproRemote export ${TARGET_DISTRIBUTION}
else
  repreproRemote "checkupdate $TARGET_DISTRIBUTION 2>&1 | grep -E '(upgraded|newly installed)' | sort -u"
fi

# remove remote pkgtools
removeRemotePkgtools

# generate changelog
diffCommand="python3 ${PKGTOOLS}/changelog.py --log-level info --product ${TARGET_DISTRIBUTION/-*} --distribution $TARGET_DISTRIBUTION --tag-type sync --create-tags"
if [ -n "$simulate" ] ; then
  diffCommand="$diffCommand --simulate"
fi
$diffCommand >| $CHANGELOG_FILE
cat $CHANGELOG_FILE
