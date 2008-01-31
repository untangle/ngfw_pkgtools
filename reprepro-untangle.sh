#! /bin/bash

GPG_TTY=`tty` GNUPGHOME=/root/.gnupg eval `sudo cat /root/.gnupg/gpg-agent-info` sudo /usr/bin/reprepro $@
