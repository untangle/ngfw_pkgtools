#! /bin/bash

GPG_TTY=`tty` GNUPGHOME=/root/.gnupg eval `cat /root/.gnupg/gpg-agent-info` sudo /usr/bin/reprepro $@
