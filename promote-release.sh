#! /bin/bash

usage() {
  echo "Usage: $0 [-s] [-w]  [-A architecture] [-C <component>] [-T (dsc|udeb|deb)] [-m] -r <repository> <fromDistribution> <toDistribution>"
  echo "-s : simulate"
  echo "-m : manifest"
  echo "-w : wipe out <toDistribution> first"
  echo "-C <component>    : only act on component <component>"
  echo "-T (dsc,udeb,deb) : only act on source/udeb/deb packages"
  echo "-A <arch>         : only act on architecture <arch>"
  exit 1
}

while getopts "A:T:C:shwr:d:m" opt ; do
  case "$opt" in
    s) simulate=1 && EXTRA_ARGS="$EXTRA_ARGS -s" ;;
    r) REPOSITORY=$OPTARG ;;
    m) MANIFEST=1 ;;
    C) COMPONENT="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -C $COMPONENT" ;;
    A) ARCHITECTURE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -A $ARCHITECTURE" ;;
    T) TYPE="$OPTARG" && EXTRA_ARGS="$EXTRA_ARGS -T $TYPE" ;;
    w) WIPE_OUT_TARGET=1 ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))
if [ ! $# = 2 ] ; then
  usage
fi

FROM_DISTRIBUTION=$1
TO_DISTRIBUTION=$2

[ -z "$REPOSITORY" -o -z "$FROM_DISTRIBUTION" -o -z "$TO_DISTRIBUTION" ] && usage && exit 1
#[ "$FROM_DISTRIBUTION" = "nightly" ] && echo "You really do not want to promote nightly" && exit 2

pkgtools=`dirname $0`
tmp_base=/tmp/promotion-$REPOSITORY-$FROM_DISTRIBUTION-to-$TO_DISTRIBUTION-`date -Iminutes`
/bin/rm -f ${tmp_base}*
diffCommand="$pkgtools/apt-chroot-utils/compare-sources.py `hostname`,$REPOSITORY,$FROM_DISTRIBUTION `hostname`,$REPOSITORY,$TO_DISTRIBUTION $tmp_base"

. $pkgtools/release-constants.sh

##########
# MAIN
/bin/rm -f ${tmp_base}*
[ -n "$MANIFEST" ] && python $diffCommand
# in case the previous diff failed, we still want mutt to email out
# the notice
[ -f ${tmp_base}*.txt ] || touch ${tmp_base}.txt
[ -f ${tmp_base}*.csv ] || touch ${tmp_base}.csv

# wipe out target distribution first
[ -n "$WIPE_OUT_TARGET" ] && $pkgtools/remove-packages.sh $EXTRA_ARGS -r $REPOSITORY -d $TO_DISTRIBUTION

$pkgtools/copy-packages.sh $EXTRA_ARGS -r $REPOSITORY $FROM_DISTRIBUTION $TO_DISTRIBUTION

# remove the sources for hades 
#$pkgtools/remove-packages.sh -r $REPOSITORY -d $TO_DISTRIBUTION -c premium -t dsc

if [ -z "$simulate" ] && [ -n "$MANIFEST" ] ; then
  attachments="-a ${tmp_base}*.txt -a ${tmp_base}*.csv"
  mutt -F $MUTT_CONF_FILE $attachments -s "[Distro Promotion] $REPOSITORY: $FROM_DISTRIBUTION promoted to $TO_DISTRIBUTION" $RECIPIENT <<EOF
Effective `date`.

Attached are the diff files for this promotion, generated by running
the following command prior to actually promoting:

  $diffCommand

--ReleaseMaster ($USER@`hostname`)
EOF
fi

/bin/rm -f ${tmp_base}*