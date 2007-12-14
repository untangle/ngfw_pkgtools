#! /bin/bash

# FIMXE: does it get any nastier than this ??
# make that a CGI on mephisto, for fucksake...

REMOTE_USER="root@mephisto"
KEY_PART="-i ./qabuildbot.dsa"
TMP_DIR=/tmp/mephisto-proxy_$$

ssh $KEY_PART $REMOTE_USER "rm -fr $TMP_DIR ; mkdir $TMP_DIR"
scp $KEY_PART *sh $REMOTE_USER:$TMP_DIR
ssh $KEY_PART $REMOTE_USER "cd $TMP_DIR ; $@"
ssh $KEY_PART $REMOTE_USER rm -fr $TMP_DIR