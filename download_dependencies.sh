#! /bin/bash

usage() {
  echo "$0 <sources> <package> [<package> ...]"
  echo
  echo "Downloads the listed packages and their dependencies,"
  echo "from the given comma-separated list of mirrors"
  echo
  echo "Example:"
  echo "  $0 'deb http://http.us.debian.org/debian lenny main, deb http://mephisto/public/lenny nightly main upstream' mawk"
}

if [ $# -lt 2 ] ; then
  usage
  exit 1
fi

sources=$1
shift

tmpDir=`mktemp -t -d XXXXXXXXXXXXX`
sourcesFile=$tmpDir/sources.list
downloadsDir=$tmpDir/downloads

APTOPTS="-o Dir::State::status=/dev/null -o Dir::Cache=$tmpDir -o Dir::Etc::SourceList=$sourcesFile -o Dir::State=$tmpDir -o Debug::NoLocking=1"

echo $sources | perl -pe 's|\s*,\s*|\n|' >| $sourcesFile
mkdir -p $tmpDir/lists/partial $tmpDir/archives/partial $downloadsDir

echo -n "Updating sources..."
apt-get $APTOPTS -q update > /dev/null 2>&1
echo " done"

deps=`apt-rdepends $APTOPTS $@ 2> /dev/null | awk '/Depends:/ {print $2}' | sort -u | xargs`

if [ -n "$deps" ] ; then
  echo "Dependencies are: $deps"
  pushd $downloadsDir > /dev/null
  echo -n "Downloading..."
  aptitude $APTOPTS download $@ $deps > /dev/null 2>&1
  echo " done"
  rename 's/%3a/:/' *
  popd > /dev/null
  echo "Your packages are in $downloadsDir"
else
  echo "No dependencies found."
fi

