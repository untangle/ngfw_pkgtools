#!/bin/bash

set -e

## CLI parameters
DEB=$1

## main
script_name=$(basename $0)
tmp_dir=$(mktemp -d /tmp/${script_name/.*}-XXXXXXX)
control_dir=$tmp_dir/control_dir
timestamp=$(date --iso-8601=seconds | perl -pe 's/[-+][\d:]+$// ; s/[-:]//g')
version_suffix="+untangle.$timestamp"

# get name of the control archive
control_archive=$(ar t $DEB | grep -P '^control')

# get corresponding tar compression flag
case $control_archive in
  *bz2) compression_flag="j" ;;
  *gz) compression_flag="z" ;;
  *xz) compression_flag="J" ;;
  *) echo "unrecognized compression algorithm for $control_archive"
     exit 1 ;; 
esac

# extract control data
mkdir $control_dir
ar p $DEB $control_archive | tar -C $control_dir -x${compression_flag}f -

# remove Essential flag and update version
perl -i -ne 's/(Version: .+)/$1'$version_suffix'/; print unless m/^Essential:/' $control_dir/control

# repack control data
tar -C $control_dir -c${compression_flag}f $tmp_dir/$control_archive .

# derive filename for new package file
package=$(awk '/Package: / {print $2}' $control_dir/control)
version=$(awk '/Version: / {print $2}' $control_dir/control)
architecture=$(awk '/Architecture: / {print $2}' $control_dir/control)
new_deb=${package}_${version}_${architecture}.deb

# initialize new package file
cp $DEB $tmp_dir/$new_deb

# update control data
pushd $tmp_dir > /dev/null
ar r $new_deb $control_archive
popd > /dev/null

# local copy 
mv $tmp_dir/$new_deb .
echo "new deb file is $new_deb"

# cleanup
rm -fr $tmp_dir
