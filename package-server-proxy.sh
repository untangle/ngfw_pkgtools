#! /bin/bash

# FIMXE: does it get any nastier than this ??
# make that a CGI on package-server, for fucksake...

PKGTOOLS_DIR=$(readlink -f $(dirname $0))
REMOTE_HOST="package-server.untangle.int"
SSH_OPTIONS="-o StrictHostKeyChecking=no"
TMP_DIR=/tmp/package-server-proxy_$$

ssh $SSH_OPTIONS $REMOTE_HOST "rm -fr $TMP_DIR ; mkdir $TMP_DIR"
scp $SSH_OPTIONS -q $PKGTOOLS_DIR/$1 $REMOTE_HOST:$TMP_DIR
ssh $SSH_OPTIONS $REMOTE_HOST "cd $TMP_DIR ; $@"
rc=$?
ssh $SSH_OPTIONS $REMOTE_HOST rm -fr $TMP_DIR

exit $rc
