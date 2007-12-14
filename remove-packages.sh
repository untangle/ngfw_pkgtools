#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> [-c <component>] [-t (dsc|deb)]"
  exit 1
}

while getopts "r:d:c:t:h" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    c) [ -n "$OPTARG" ] && COMPONENT="-C $OPTARG" ;;
    t) [ -n "$OPTARG" ] && TYPE="-T $OPTARG" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION" ] && usage && exit 1

. release-constants.sh

list=`${REPREPRO_BASE_COMMAND} listfilter ${DISTRIBUTION} Package | awk '{print $2}'`
[ -n "$list" ] && echo "$list" | xargs ${REPREPRO_BASE_COMMAND} remove ${DISTRIBUTION}
