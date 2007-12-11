#!/bin/bash

### CLI args
while getopts r:b:d:ue option ; do
  case "$option" in
    r) TARGET_REP="$OPTARG" ;;
    b) BUILD_DIR="$OPTARG" ;;
    d) DISTRIBUTION="$OPTARG" ;;
    u) RELEASE="release" ;;
    e) CHECK_EXISTENCE="check-existence" ;;
  esac
done

processResult() {
  result=$1
  [ $result = 0 ] && resultString="SUCCESS" || resultString="ERROR"
  echo "**** ${resultString}: make in $directory exited with return code $result"
  echo
  echo "# ======================="
  let results=results+result
  popd
}

### a few variables
FILE_IN="build-order.txt"
PKGTOOLS_HOME=`dirname $(readlink -f $0)`
results=0

### main
# cd into the main trunk
cd "${BUILD_DIR}"

# first grab the content of the build-order.txt file
build_dirs=()
while read line ; do
  build_dirs[${#build_dirs[*]}]="$line"
done < $FILE_IN

# now cd into each dir in build_dirs and make
for directory in "${build_dirs[@]}" ; do
  case "$directory" in
    \#*) ;; # comment
    "") ;; # empty line
    *) # yes
      echo 
      echo "# $directory"

      # cd into it, and attempt to build
      pushd "$directory"
      make -f $PKGTOOLS_HOME/Makefile DISTRIBUTION=$DISTRIBUTION REPOSITORY=$TARGET_REP version ${CHECK_EXISTENCE}
      result=$?      
      [ $result = 2 ] && processResult($result) && continue
      make -f $PKGTOOLS_HOME/Makefile DISTRIBUTION=$DISTRIBUTION REPOSITORY=$TARGET_REP source pkg-chroot ${RELEASE}
      result=$?
      processResult($result) ;;
  esac
done

exit $results
