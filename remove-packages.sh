#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> [-s] [-e <regex>|-n <negate_regex>] [-c <component>] [-t (dsc|deb)]"
  echo "-s             : simulate"
  echo "-e <regex>     : only act on packages matching <regexp>"
  echo "-n <regex>     : exclude packages matching <regexp>"
  echo "-c <component> : only act on <component>"
  echo "-c (dsc,deb)   : only act on source or binary packages"
  exit 1
}

while getopts "r:d:c:e:n:t:hs" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    e) REGEX="-E $OPTARG" ;;
    n) NREGEX="-v -E $OPTARG" ;;
    s) SIMULATE=true ;;
    c) COMPONENT="-C $OPTARG" ;;
    t) TYPE="-T $OPTARG" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION" ] && usage && exit 1
[ -n "$REGEX" -a -n "$NREGEX" ] && usage && exit 1
[ -z "$REGEX" -a -z "$NREGEX" ] && REGEX="-E ."

. `dirname $0`/release-constants.sh

list=`${REPREPRO_BASE_COMMAND} listfilter ${DISTRIBUTION} Package | grep $REGEX $NREGEX | sort -u`

if [ -n "$SIMULATE" ] ; then
  echo "$list"
else
  [ -n "$list" ] && echo "$list" | awk '{print $2}' | xargs ${REPREPRO_BASE_COMMAND} remove ${DISTRIBUTION}
fi
