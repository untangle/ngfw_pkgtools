#!/bin/sh

# usage...
if [ $# -lt 1 ] || [ $# -gt 2 ] ; then 
  echo "Usage: $0 distribution [version ]" && exit 1
fi

rm -f debian/changelog.dch

# CL args
distribution=${1}

if [ -z "$2" ] ; then
  if [ -f ../VERSION ] ; then
    versionFile=../VERSION
  elif [ -f ./resources/VERSION ] ; then # Hades
    versionFile=./resources/VERSION
  else
    versionFile=../../VERSION
  fi

  # get 2 values from SVN: last changed revision & timestamp for the
  # current directory
  revision=`svn info --recursive . | awk '/Last Changed Rev: / { print $4 }' | sort -n | tail -1`
  timestamp=`svn info --recursive . | awk '/Last Changed Date:/ { gsub(/-/, "", $4) ; print $4 }' | sort -n | tail -1`

  # this is how we figure out if we're up-to-date or not
  hasLocalChanges=`svn status | grep -v -E '^([X?]|Fetching external item into|Performing status on external item at|$)'`

  # this is the base version; it will be tweaked a bit oif need be:
  # - append a local modification marker is we're not up to date
  # - prepend the upstream version if UNTANGLE-KEEP-UPSTREAM-VERSION exists
  baseVersion=`cat $versionFile`~svn${timestamp}r${revision}

  if [ -f UNTANGLE-KEEP-UPSTREAM-VERSION ] ; then
    previousUpstreamVersion=`dpkg-parsechangelog | awk '/Version: / { gsub(/-.*/, "", $2) ; print $2 }'`
    baseVersion=${previousUpstreamVersion}+${baseVersion}
  fi

  if [ -z "$hasLocalChanges" ] ; then
    version=$baseVersion
  else
    version=${baseVersion}+$USER`date +"%Y%m%dT%H%M%S"`
    distribution=$USER
  fi
else # force version
  version=$2
fi

version=${version}-1

echo "Setting version to \"${version}\", distribution to \"$distribution\""
DEBEMAIL="${DEBEMAIL:-${USER}@untangle.com}" dch -v ${version} -D ${distribution} "auto build"
# check changelog back in if version was forced
[ -n "$2" ] && svn commit debian/changelog -m "Forcing version to $version"
echo " done."


