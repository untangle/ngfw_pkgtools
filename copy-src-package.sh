#! /bin/bash

set -e

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> -f <distributionFrom> -s <sourcePkg> -v <version> [-h host]"
  exit 1
}

while getopts "r:d:f:s:A:v:h?" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    h) HOST=$OPTARG ;;
    s) SOURCE=$OPTARG ;;
    v) VERSION=$OPTARG ;;
    f) DISTRIBUTION_FROM=$OPTARG ;;
    h|\?) usage ;;
  esac
done

ARCH=$(dpkg-architecture -qDEB_BUILD_ARCH)
HOST=${HOST:-mephisto}

[ -z "$REPOSITORY" ] || [ -z "$DISTRIBUTION" ] || [ -z "$DISTRIBUTION_FROM" ] && usage
[ -z "$VERSION" ] || [ -z "$SOURCE" ] && usage

manifest="${SOURCE}_${VERSION}_${ARCH}.${REPOSITORY}_${DISTRIBUTION}.copy"
echo "copysrc ${DISTRIBUTION} ${DISTRIBUTION_FROM} ${SOURCE}" > $manifest

echo "About to upload: $(cat $manifest)"

lftp -e "set net:max-retries 1 ; cd $REPOSITORY/incoming ; put $manifest ; exit" $HOST
rm -f $manifest
