#! /bin/bash

set -e

INDEX=www/index.html
#FILE=history.txt

cd $(dirname $(readlink -f $0))

pushd lintian.git > /dev/null
[ -d doc/lintian.html ] || fakeroot debian/rules generate-docs
popd > /dev/null

lintian.git/reporting/harness -i

# echo -n `date +"%Y-%m-%dT%H:%M"` >> $FILE
# perl -ne 'print "," . $1 if $_ =~ /(\d+) \(.+\)/' $INDEX >> $FILE
# echo >> $FILE

# gnuplot report.gplot
