#! /bin/sh

usage() {
  echo "$0 <fromDir> <toDir>"
  echo "fromDir was obtained from svn co svn://chef/branch/prod/release-n.m/work"
  echo "toDir was obtained from svn co svn+ssh://svn.untangle.com/usr/local/svn/branch/prod/release-n.m"
}

if [ $# != 2 ] || [ ! -d "$1" ] || [ ! -d "$2" ] ; then
  usage
  exit 1
fi

fromDir=$1
toDir=$2

# get latest from private svn
svn up $fromDir/work

# sync that to locally checked-out public svn
rsync -aH --delete --exclude .svn $fromDir/work/ $toDir/

# schedule those changes
pushd $toDir
svn stat | while read s name ; do 
  case $s in
    \?) svn add $name ;;
    \!) svn rm $name ;;
  esac
done

# commit them
svn commit

popd
