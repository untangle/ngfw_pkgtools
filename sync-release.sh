#! /bin/bash

usage() {
  echo "Usage: $0 [-s] -r <repository> -d <distribution>"
  echo "-s : simulate"
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
if [ ! $# = 0 ] ; then
  usage
fi

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION" ] && usage && exit 1

. `dirname $0`/release-constants.sh

# MAIN
if [ -z "$simulate" ] ; then
  $SSH_COMMAND /etc/init.d/untangle-gpg-agent start
  $REPREPRO_REMOTE_COMMAND --noskipold update ${DISTRIBUTION}
  # also remove source packages for premium
  $SSH_COMMAND ./remove-packages.sh -r ${REPOSITORY} -d ${DISTRIBUTION} -t dsc -c premium
  $SSH_COMMAND /etc/init.d/untangle-gpg-agent stop
else
  $REPREPRO_REMOTE_COMMAND checkupdate $DISTRIBUTION | grep upgraded
  $SSH_COMMAND ./remove-packages.sh -r ${REPOSITORY} -d ${DISTRIBUTION} -t dsc -c premium -s
fi
