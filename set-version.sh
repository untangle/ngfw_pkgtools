#! /bin/bash

# set -x

# usage...
if [ ! $# -eq 3 ] ; then 
  echo "Usage: $0 distribution VERSION=[version] REPOSITORY=[repository]" && exit 1
fi

# env/constants
export TZ="US/Pacific"
export DEBEMAIL="${DEBEMAIL:-buildbot@untangle.com}"
export DEBFULLNAME="${DEBFULLNAME:-Untangle Buildbot}"

# CL args
distribution=${1}
version=${2/VERSION=}
versionGiven=$version
repository=${3/REPOSITORY=}

[ -z "${repository}" ] && repository=`$0/getPlatform.sh`

osdist=unknown
case $repository in
  sarge|etch|lenny|sid) osdist=debian ;;
  feisty|gutsy|intrepid|hardy) osdist=ubuntu ;;
esac

rm -f debian/changelog.dch
previousVersion=`dpkg-parsechangelog 2> /dev/null | awk '/Version: / { print $2 }'`
previousUpstreamVersion=`dpkg-parsechangelog 2> /dev/null | awk '/Version: / { gsub(/-.*/, "", $2) ; print $2 }'`

if [ -z "$version" ] ; then
  # not exactly kosher, but I'll contend that incVersion.sh is only
  # called from the Makefile :>
  versionFile=`dirname $0`/resources/VERSION

  # get some values from VCS: branch, last changed revision, timestamp
  # for the current directory

  # new-style source package are not directly under version
  # control, but their parent dir is
  [[ $(pwd) == */ngfw_upstream/* ]] && d=.. || d=.
  revision=$(git log -n 1 --format="%h" -- $d)

  # convert commit date to debian/changelog format
  timestampDch="$(git log -n 1 --date=format-local:'%a, %d %b %Y %T %z' --format='%cd' -- $d)"

  # convert commit date to an ISO timestamp of the form
  # "2016-09-13T23:46:56-0700"
  timestamp="$(git log -n 1 --date=iso-strict-local --format='%cd' -- $d)"
  # ... and then to "20160913T234656", accounting for weird
  # timezone format&separator
  timestamp=$(echo $timestamp | perl -pe 's/[-+][\d:]+$// ; s/[-:]//g')

  # is this a clean git tree ?
  hasLocalChanges=$(git diff-index --name-only HEAD -- .)

  # this is the base version; it will be tweaked a bit if need be:
  # - append a local modification marker is we're not up to date
  # - prepend the upstream version if UNTANGLE-KEEP-UPSTREAM-VERSION exists
  baseVersion=$(cat $versionFile).${timestamp}.${revision}

  if [ -f UNTANGLE-KEEP-UPSTREAM-VERSION ] ; then
    baseVersion=${previousUpstreamVersion}+${baseVersion}
  elif [ -f UNTANGLE-FORCE-UPSTREAM-VERSION ] ; then
    # if we find UNTANGLE-FORCE-UPSTREAM-VERSION, do nothing as it
    # means we want to build an upstream package without modifying it
    # at all.
    baseVersion=${previousVersion}
  fi

  if [ -z "$hasLocalChanges" ] ; then
    version=$baseVersion
  else
    echo -e "The changes were:\n$hasLocalChanges"
    version=${baseVersion}+localdiff`date +"%Y%m%dT%H%M%S"`
  fi

  if [ ! -f UNTANGLE-FORCE-UPSTREAM-VERSION ] ; then  # FIXME: ugly, but will do for now
    version=${version}-1
  fi
else # force version
  if [ -f UNTANGLE-KEEP-UPSTREAM-VERSION ] ; then
    previousUpstreamVersion=`dpkg-parsechangelog | awk '/Version: / { gsub(/-.*/, "", $2) ; print $2 }'`
    version=${previousUpstreamVersion}+${version}
  fi
  case "$version" in
    *-*) ;; # the user did supply a Debian revision
    *)   version=${version}-1 ;;
  esac
fi

version=${version}${repository}

# setup dch
dch=$(mktemp /tmp/dch-XXXXX)
/bin/cp -f /usr/bin/dch $dch
chmod 755 $dch
sed -i -e '/garbage/d' $dch

# write new version
echo "Setting version='${version}' distribution='$distribution' timestamp='$timestampDch'"
dchArgs="--preserve -v ${version} -D ${distribution}"
$dch $dchArgs "auto build" 2> /dev/null

# rewrite debian/changelog timestamp to commit timestamp
gawk -v ts="$timestampDch" 'NR == 5 { gsub(/\s\s.+/, "  " ts, $0) } { print }' debian/changelog > debian/changelog.dch
mv -f debian/changelog.dch debian/changelog

rm -f $dch
echo "... done"
