#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> -d <distribution> [-s] [-e <regex>|-n <negate_regex>] [-A architecture] [-C <component>] [-T (dsc|udeb|deb)]"
  echo "-s                : simulate"
  echo "-e <regex>        : only act on packages matching <regexp>"
  echo "-n <regex>        : exclude packages matching <regexp>"
  echo "-C <component>    : only act on component <component>"
  echo "-T (dsc,udeb,deb) : only act on source/udeb/deb packages"
  echo "-A <arch>         : only act on architecture <arch>"
  exit 1
}

while getopts "r:d:A:C:T:e:n:hs" opt ; do
  case "$opt" in
    r) REPOSITORY=$OPTARG ;;
    d) DISTRIBUTION=$OPTARG ;;
    e) REGEX="-E $OPTARG" ;;
    n) NREGEX="-v -E $OPTARG" ;;
    s) SIMULATE=true ;;
    C) COMPONENT="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -C $COMPONENT" ;;
    A) ARCHITECTURE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -A $ARCHITECTURE" ;;
    T) TYPE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -T $TYPE" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))

[ -z "$REPOSITORY" -o -z "$DISTRIBUTION" ] && usage && exit 1
[ -n "$REGEX" -a -n "$NREGEX" ] && usage && exit 1
[ -z "$REGEX" -a -z "$NREGEX" ] && REGEX="-E ."

. `dirname $0`/release-constants.sh

list=`repreproLocal $EXTRA_ARGS listfilter ${DISTRIBUTION} Package | grep $REGEX $NREGEX | awk '{print $2}' | sort -u`

if [ -n "$SIMULATE" ] ; then
  echo "$list"
else
  # can't use "xargs functionName"
  [ -z "$list" ] || echo "$list" | xargs $PKGTOOLS/${REPREPRO_COMMAND} remove ${DISTRIBUTION}
fi
