#! /bin/sh

set -e

SVN_SERVER="chef"

GIT_DEFAULT_BRANCH="origin/master"
GIT_REMOTE_TRUNK=".git/refs/remotes/trunk"

# main
module=$(git config --get remote.origin.url | perl -pe 's|.*/(.+)\.git|$1|')

case $module in
  src|pkgs) dir=work/$module ;;
  *) dir=$module ;;   
esac

git svn init -T $dir \
             -b branch/prod/*/$dir \
             -t tags/*/$dir \
             svn://$SVN_SERVER

git show $GIT_DEFAULT_BRANCH | awk '{print $2 ; exit}' >| $GIT_REMOTE_TRUNK

git svn fetch -r 26543 # starting at 7.3 branching

git remote rm origin
