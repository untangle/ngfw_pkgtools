#! /bin/bash

set -e

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> -f <distributionFrom> -s <sourcePkg> -v <version> [-h host] [-A architecture]"
  echo -e "\t-A <arch> : only act on architecture <arch>"
  exit 1
}

while getopts "r:d:f:s:A:v:h?" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    h) HOST=$OPTARG ;;
    A) ARCH="$OPTARG" ;;
    s) SOURCE=$OPTARG ;;
    v) VERSION=$OPTARG ;;
    f) DISTRIBUTION_FROM=$OPTARG ;;
    h|\?) usage ;;
  esac
done
ARCH=${ARCH:-i386}
HOST=${HOST:-mephisto}

[ -z "$REPOSITORY" ] || [ -z "$DISTRIBUTION" ] || [ -z "$DISTRIBUTION_FROM" ] && usage
[ -z "$VERSION" ] || [ -z "$SOURCE" ] && usage

echo "About to upload:"

manifest="${SOURCE}_${VERSION}_${ARCH}.${REPOSITORY}_${DISTRIBUTION}.copy"
echo "copysrc ${DISTRIBUTION} ${DISTRIBUTION_FROM} ${SOURCE}" > $manifest

lftp -e "set net:max-retries 1 ; cd $REPOSITORY/incoming ; put $manifest ; exit" $HOST
rm -f $manifest
