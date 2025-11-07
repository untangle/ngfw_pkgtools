#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> -p <sourcePkg <distributionFrom> <distributionTo>"
}

while getopts "r:p:" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    p) SOURCE_PKG=$OPTARG ;;
    h|\?) usage ;;
  esac
done
shift $(($OPTIND - 1))

FROM_DISTRIBUTION=$1
TO_DISTRIBUTION=$2

HOST="package-server"

[ -z "$REPOSITORY" -o -z "$FROM_DISTRIBUTION" -o -z "$TO_DISTRIBUTION" -o -z "$SOURCE_PKG" ] && usage && exit 1

. $(dirname $0)/lib/constants-update.sh

$PKGTOOLS/${REPREPRO_COMMAND} copysrc ${FROM_DISTRIBUTION} ${TO_DISTRIBUTION} ${SOURCE_PKG}

