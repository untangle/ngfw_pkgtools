#! /bin/bash

usage() {
  echo "$0 <sources> <package> [<package> ...]"
  echo
  echo "Downloads the listed packages and their dependencies,"
  echo "from the given comma-separated list of mirrors"
  echo
  echo "Example:"
  echo "  $0 [-n] 'deb http://http.us.debian.org/debian lenny main, deb http://mephisto/public/lenny nightly main upstream' mawk [package2 ...]"
  exit 1
}

while getopts "nh" opt ; do
  case "$opt" in
    n) NO_DEPENDENCIES="true" ;;
    h) usage ;;
    \?) usage ;;
  esac
done
shift $(($OPTIND - 1))

if [ $# -lt 2 ] ; then
  usage
fi

sources=$1
shift
for package in $@ ; do
  package=`basename $package`
  packages="$packages ${package/_*}"
done

tmpDir=`mktemp -t -d XXXXXXXXXXXXX`
sourcesFile=$tmpDir/sources.list
downloadsDir=$tmpDir/downloads

APTOPTS="-o Dir::State::status=/dev/null -o Dir::Cache=$tmpDir -o Dir::Etc::SourceList=$sourcesFile -o Dir::State=$tmpDir -o Debug::NoLocking=1"

echo $sources | perl -pe 's|\s*,\s*|\n|' >| $sourcesFile
mkdir -p $tmpDir/lists/partial $tmpDir/archives/partial $downloadsDir

echo -n "Updating sources..."
apt-get $APTOPTS -q update > /dev/null 2>&1
echo " done"

if [ -z "$NO_DEPENDENCIES" ] ; then
  packages="$packages `apt-rdepends $APTOPTS $packages 2> /dev/null | awk '/Depends:/ {print $2}' | sort -u | xargs`"
fi

echo "Dependencies are: $packages"
pushd $downloadsDir > /dev/null
echo -n "Downloading..."
aptitude $APTOPTS download $packages # > /dev/null 2>&1
echo " done"
rename 's/%3a/:/' * # no http encoding
popd > /dev/null
echo "Your packages are in $downloadsDir"
