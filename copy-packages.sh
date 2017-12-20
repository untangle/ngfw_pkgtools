#! /bin/bash

usage() {
  echo "Usage: $0 -r <repository> [-s] [-e <regex>|-n <negate_regex>]  [-A architecture] [-C <component>] [-T (dsc|udeb|deb)] <fromDistribution> <toDistribution>"
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

FROM_DISTRIBUTION=$1
TO_DISTRIBUTION=$2

[ -z "$REPOSITORY" -o -z "$FROM_DISTRIBUTION" -o -z "$TO_DISTRIBUTION" ] && usage && exit 1
[ -n "$REGEX" -a -n "$NREGEX" ] && usage && exit 1
[ -z "$REGEX" -a -z "$NREGEX" ] && REGEX="-E ."

. $(dirname $0)/release-constants.sh

case $FROM_DISTRIBUTION in
  */snapshots/*)
    parent=`echo $FROM_DISTRIBUTION | perl -pe 's|/snapshots/.+||'`
    date=`echo $FROM_DISTRIBUTION | perl -pe 's|.+/snapshots/(.+)|$1|'`
    # if any extra arg is used, this will wail with an informative
    # message, which is the Proper Behavior(TM)
    list=`repreproLocal dumpreferences | perl -ne 'print $1 . "\n" if $_ =~ m|^s='$parent=$date'.+/(.+?)_.*\.deb|' | grep $REGEX $NREGEX | sort -u`
    FROM_DISTRIBUTION="s=$parent=$date"
    copy="restore"
    FROM_DISTRIBUTION="$date" ;;
  *)
    list=`repreproLocal listfilter ${FROM_DISTRIBUTION} Package | grep $REGEX $NREGEX | awk '{print $2}' | sort -u`
    copy="copy" ;;
esac

if [ -n "$SIMULATE" ] ; then
  echo "$list"
else
  # can't use "xargs functionName"
  [ -z "$list" ] || echo "$list" | xargs $PKGTOOLS/${REPREPRO_COMMAND} $EXTRA_ARGS $copy ${TO_DISTRIBUTION} ${FROM_DISTRIBUTION}
fi
