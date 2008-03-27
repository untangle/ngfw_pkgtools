#! /bin/bash

usage() {
  echo "Usage: $0 [-s] [-w] -r <repository> <fromDistribution> <toDistribution>"
  echo "-s : simulate"
  echo "-w : wipe out <toDistribution> first"
  exit 1
}

while getopts "shr:d:" opt ; do
  case "$opt" in
    s) simulate=1 && EXTRA_ARGS="-s" ;;
    r) REPOSITORY=$OPTARG ;;
    w) WIPE_OUT_TARGET=1 ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 2 ] ; then
  usage
fi

FROM_DISTRIBUTION=$1
TO_DISTRIBUTION=$2

[ -z "$REPOSITORY" -o -z "$FROM_DISTRIBUTION" -o -z "$TO_DISTRIBUTION" ] && usage && exit 1

pkgtools=`dirname $0`

. $pkgtools/release-constants.sh

##########
# MAIN

# wipe out target distribution first
[ -n "$WIPE_OUT_TARGET" ] && $pkgtools/remove-packages.sh $EXTRA_ARGS -r $REPOSITORY -d $TO_DISTRIBUTION

# actual promotion
$pkgtools/copy-packages.sh $EXTRA_ARGS -r $REPOSITORY $FROM_DISTRIBUTION $TO_DISTRIBUTION

# remove the sources for hades 
#$pkgtools/remove-packages.sh $EXTRA_ARGS -r $REPOSITORY -d $TO_DISTRIBUTION -c premium -t dsc

echo -e "Effective `date`\n\n--ReleaseMaster ($USER@`hostname`)" | mailx -s "[$REPOSITORY] *$FROM_DISTRIBUTION* promoted to *$TO_DISTRIBUTION*" seb@untangle.com