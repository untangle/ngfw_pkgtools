#! /bin/bash

# FIMXE: does it get any nastier than this ??
# make that a CGI on mephisto, for fucksake...

KEY="./qabuildbot.dsa"
REMOTE_USER="root@mephisto"
SSH_KEY_OPTION="-i $KEY"
TMP_DIR=/tmp/mephisto-proxy_$$

chmod 600 $KEY
ssh $SSH_KEY_OPTION $REMOTE_USER "rm -fr $TMP_DIR ; mkdir $TMP_DIR"
scp $SSH_KEY_OPTION *sh $REMOTE_USER:$TMP_DIR
ssh $SSH_KEY_OPTION $REMOTE_USER "cd $TMP_DIR ; $@"
ssh $SSH_KEY_OPTION $REMOTE_USER rm -fr $TMP_DIR
