#! /bin/sh

set -e

usage() {
  echo "$0 <fromUri> <toUri>"
  echo "fromUri is something like svn://chef/branch/prod/release-n.m/work"
  echo "toUri is something like svn+ssh://svn.untangle.com/usr/local/svn/branch/prod/release-n.m"
}

checkUri() {
  svn ls $1 > /dev/null 2>&1
}

if [ $# -lt 2 ] ; then
  usage
  exit 1
fi

fromUri=$1
toUri=$2
baseDir=/localhome/$USER

if ! checkUri $fromUri ; then
  echo "$fromUri does not exist"
  exit 2
fi

if ! checkUri $toUri ; then
  read -a answer -n 1 -p "$toUri does not exist, create (y/n) ? "
  echo
  if [ "$answer" = 'y' ] || [ "$answer" = 'Y' ]; then
    svn mkdir --parents -m "Adding branch $(basename $toUri)" $toUri
  else
    exit 3
  fi
fi

fromDir=$(mktemp -d $baseDir/from.XXXXXXXXXXXXXXX)

# get latest from private svn
svn co $fromUri/work $fromDir

pushd $fromDir
version=$(cat VERSION)
# get some values from SVN: last changed revision, timestamp for the
# current directory
revision=$(svn info --recursive . | awk '/Last Changed Rev: / { print $4 }' | sort -n | tail -1)
timestamp=$(svn info --recursive . | awk '/Last Changed Date:/ { gsub(/-/, "", $4) ; print $4 }' | sort -n | tail -1)
popd

# echo /usr/bin/find $fromDir -name .svn | xargs rm -fr
# exit 4

versionString=untangle_source_${version}_${timestamp}r${revision}
toDir=$baseDir/$versionString

# get latest from public svn
svn co $toUri $toDir

# sync private check-out to public check-out
rsync -aH --delete --filter='-p .svn' $fromDir/ $toDir/

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

# tarball maybe ?
if [ -n "$3" ] ; then
  pushd $baseDir
  tarball=$versionString.tar.gz
  tar cz --exclude .svn -f $tarball $versionString
  scp $tarball untangle_@frs.sourceforge.net:upload/
  popd
fi

rm -fr $fromDir $toDir
