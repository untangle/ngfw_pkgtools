#! /bin/bash

set -e

usage() {
  echo "Usage: $0 [-s] [-w]  [-A architecture] [-C <component>] [-T (dsc|udeb|deb)] -r <repository> -f <fromDistribution> -d <targetDistribution>"
  echo "-s : simulate"
  echo "-w : wipe out <toDistribution> first"
  echo "-C <component>    : only act on component <component>"
  echo "-T (dsc,udeb,deb) : only act on source/udeb/deb packages"
  echo "-A <arch>         : only act on architecture <arch>"
  echo "-r : repository to use"
  echo "-f : source distribution to promote from"
  echo "-d : target distribution (needs to be a full <product>-x.y.z)"
  exit 1
}

while getopts "A:T:C:shwr:f:d:" opt ; do
  case "$opt" in
    s) simulate=1 && EXTRA_ARGS="$EXTRA_ARGS -s" ;;
    r) REPOSITORY=$OPTARG ;;
    C) COMPONENT="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -C $COMPONENT" ;;
    A) ARCHITECTURE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -A $ARCHITECTURE" ;;
    T) TYPE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -T $TYPE" ;;
    w) WIPE_OUT_TARGET=1 ;;
    f) FROM_DISTRIBUTION=$OPTARG ;;
    d) TARGET_DISTRIBUTION=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 0 ] ; then
  usage
fi

[ -z "$REPOSITORY" -o -z "$FROM_DISTRIBUTION" -o -z "$TARGET_DISTRIBUTION" ] && usage && exit 1

##########
# MAIN

# include common variables
. $(dirname $0)/lib/constants.sh
CHANGELOG_FILE="promotion.txt"

# start with a clean changelog, as the one from the previous run might
# still be present
echo >| $CHANGELOG_FILE

# wipe out target distribution first
[ -n "$WIPE_OUT_TARGET" ] && ${PKGTOOLS}/remove-packages.sh $EXTRA_ARGS -r $REPOSITORY -d $TARGET_DISTRIBUTION

${PKGTOOLS}/copy-packages.sh $EXTRA_ARGS -r $REPOSITORY $FROM_DISTRIBUTION $TARGET_DISTRIBUTION

# generate changelog
diffCommand="python3 ${PKGTOOLS}/changelog.py --log-level info --product ${TARGET_DISTRIBUTION/-*} --distribution $TARGET_DISTRIBUTION --tag-type promotion --create-tags"
if [ -n "$simulate" ] ; then
  diffCommand="$diffCommand --simulate"
fi
$diffCommand >| $CHANGELOG_FILE
cat $CHANGELOG_FILE
