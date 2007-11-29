#! /bin/bash

GPG_TTY=`tty` GNUPGHOME=/root/.gnupg eval `cat /root/.gnupg/gpg-agent-info` /usr/bin/reprepro $@
