#! /bin/bash

usage() {
  echo "Usage: $0 [-s|--simulate] -r <repository> -d <distribution>"
  exit 1
}

while getopts "shr:d:" opt ; do
  case "$opt" in
    s) simulate=1 ;;
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 1 ] ; then
  usage
fi

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION" ] && usage && exit 1

. release-constants.sh

# MAIN
if [ -z "$simulate" ] ; then
  $REPREPRO_REMOTE_COMMAND update ${DISTRIBUTION}
  # also remove source packages for premium
  # FIXME: a bit of redundancy with remove-packages.sh
  $SSH_COMMAND "$REPREPRO_BASE_COMMAND -T dsc -C premium listfilter ${DISTRIBUTION} Package | awk '{print $2}' | xargs $REPREPRO_BASE_COMMAND -T dsc -C premium remove ${DISTRIBUTION}"
else
  $REPREPRO_REMOTE_COMMAND checkupdate $DISTRIBUTION | grep upgraded
fi
