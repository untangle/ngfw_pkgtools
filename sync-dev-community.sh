#! /bin/sh

set -e

usage() {
  echo "$0 <fromUri> <toUri>"
  echo "fromUri is something like svn://chef/branch/prod/release-n.m/work"
  echo "toUri is something like svn+ssh://svn.untangle.com/usr/local/svn/branch/prod/release-n.m"
}

if [ $# -lt 2 ] ; then
  usage
  exit 1
fi

fromUri=$1
toUri=$2

baseDir=/localhome/$USER
fromDir=$(mktemp -d $baseDir/from.XXXXXXXXXXXXXXX)

# get latest from private svn
svn co $fromUri/work $fromDir

pushd $fromDir
# FIXME: following code is taken straight from incVersion.sh; please
# refactor
version=$(cat VERSION)
# get some values from SVN: branch, last changed revision, timestamp for the
# current directory
url=$(svn info . | awk '/^URL:/{print $2}')
revision=$(svn info --recursive . | awk '/Last Changed Rev: / { print $4 }' | sort -n | tail -1)
timestamp=$(svn info --recursive . | awk '/Last Changed Date:/ { gsub(/-/, "", $4) ; print $4 }' | sort -n | tail -1)
popd

versionString=untangle_source_${version}_${timestamp}r${revision}
toDir=$baseDir/$versionString

# get latest from public svn
svn co $toUri $toDir

# sync that to locally checked-out public svn
rsync -aH --delete --filter='Pp .svn' $fromDir/ $toDir/

# schedule those changes
pushd $toDir
svn stat | while read s name ; do 
  case $s in
    \?) svn add $name ;;
    \!) svn rm $name ;;
  esac
done
# commit them
echo svn commit
popd

if [ -n "$3" ] ; then
  pushd $baseDir
  tar cz --exclude .svn -f $versionString.tar.gz $versionString
  popd
fi

#rm -fr $fromDir $toDir
