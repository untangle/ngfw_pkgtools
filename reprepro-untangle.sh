#! /bin/bash

GPG_TTY=`tty` GNUPGHOME=/root/.gnupg sudo /usr/bin/reprepro $@
