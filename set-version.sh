#! /bin/bash

# set -x

## functions
upstream_version() {
  echo $1 | perl -pe 's/-.*//'
}

## env/constants
export TZ="US/Pacific"
export DEBEMAIL="${DEBEMAIL:-buildbot@untangle.com}"
export DEBFULLNAME="${DEBFULLNAME:-Untangle Buildbot}"
PKGTOOLS=$(dirname $(readlink -f $0))
NGFW_VERSION=$(cat ${PKGTOOLS}/resources/VERSION)

## main

# CL args
if [ ! $# -eq 2 ] ; then 
  echo "Usage: $0 <distribution> <repository>" && exit 1
fi

DISTRIBUTION=${1}
REPOSITORY=${2}

# store existing versions
previous_version=$(dpkg-parsechangelog -S Version 2> /dev/null)
previous_upstream_version=$(upstream_version $previous_version)

######################################################################
## get some values from VCS: branch, last changed revision, timestamp
## for the current directory

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

# store the base version
version=${NGFW_VERSION}.${timestamp}.${revision}

###################################################
## handle modifiers: KEEP/FORCE, unclean tree, etc

if [ -f UNTANGLE-KEEP-UPSTREAM-VERSION ] ; then
  # preprend upstream version
  version=${previous_upstream_version}+${version}
elif [ -f UNTANGLE-FORCE-UPSTREAM-VERSION ] ; then
  # do nothing as it means we want to build an upstream package
  # without modifying it at all.
  version=${previous_version}
fi

hasLocalChanges=$(git diff-index --name-only HEAD -- .)
if [ -n "$hasLocalChanges" ] ; then
  # append a local modification marker since the git tree is not clean
  echo "Local changes detected:"
  echo $hasLocalChanges
  echo
  version=${version}+localdiff$(date +"%Y%m%dT%H%M%S")
fi

###############################################
## add the Debian revision and the repository
if [ ! -f UNTANGLE-FORCE-UPSTREAM-VERSION ] ; then
  version=${version}-1
fi

version=${version}${REPOSITORY}

##########################
## write debian/changelog

# setup dch
dch=$(mktemp /tmp/dch-XXXXX)
/bin/cp -f /usr/bin/dch $dch
chmod 755 $dch
sed -i -e '/garbage/d' $dch

# write new version to debian/changelog
echo "Setting version='${version}' distribution='$DISTRIBUTION' timestamp='$timestampDch'"
dchArgs="--preserve -v ${version} -D ${DISTRIBUTION}"
$dch $dchArgs "auto build" 2> /dev/null

# rewrite debian/changelog timestamp to commit timestamp
gawk -v ts="$timestampDch" 'NR == 5 { gsub(/\s\s.+/, "  " ts, $0) } { print }' debian/changelog >| debian/changelog.dch
mv -f debian/changelog.dch debian/changelog

rm -f $dch
echo "... done"
