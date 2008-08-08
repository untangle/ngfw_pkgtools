#! /bin/sh

dpkg-query -W --showformat='${Section} ${Priority} ${Package} ${Installed-Size}\n'
