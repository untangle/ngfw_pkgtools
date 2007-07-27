#! /bin/bash

usage() {
  echo "Usage: $0 [-s|--simulate] <release>"
  exit 1
}

while getopts "sh" opt ; do
  case "$opt" in
    s) simulate=1 ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 1 ] ; then
  usage
fi

. release-constants.sh

# MAIN
if [ -z "$simulate" ] ; then
  $REPREPRO_REMOTE_COMMAND update $1
  # also remove source packages for premium
  $SSH_COMMAND "$REPREPRO_BASE_COMMAND -T dsc -C premium listfilter $1 Package | awk '{print \$2}' | xargs $REPREPRO_BASE_COMMAND -T dsc -C premium remove $1"
else
  $REPREPRO_REMOTE_COMMAND checkupdate $1
fi
