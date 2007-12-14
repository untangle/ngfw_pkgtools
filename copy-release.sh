#! /bin/bash

usage() {
  echo "Usage: $0 [-c <component>] [-t (dsc|deb)] -r <repository> <distributionFrom> <distributionTo>"
  exit 1
}

while getopts "hr:c:t:" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG
    c) [ -n "$OPTARG" ] && COMPONENT="-C $OPTARG" ;;
    t) [ -n "$OPTARG" ] && TYPE="-T $OPTARG" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# -eq 2 ]; then
  usage
fi

DISTRIBUTION_FROM=$1
DISTRIBUTION_TO=$2

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION_FROM" -o -z "DISTRIBUTION_TO" ] && usage && exit 1
. release-constants.sh

# MAIN
$REPREPRO_BASE_COMMAND listfilter ${DISTRIBUTION_FROM} 'Package' | awk '{print $2}' | xargs $REPREPRO_BASE_COMMAND copy ${DISTRIBUTION_TO} ${DISTRIBUTION_TO}
