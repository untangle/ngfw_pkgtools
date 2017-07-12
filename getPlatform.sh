#! /bin/bash

grep -q Debian /etc/issue && i=3 || i=2
case `head -1 /etc/issue | awk "{ print \\$$i }"` in
  *sid) repository=sid ;;
  9.0) repository=stretch ;;
  8.0) repository=jessie ;;
  7.0) repository=wheezy ;;
  6.0) repository=squeeze ;;
  5.0) repository=lenny ;;
  4.0) repository=etch ;;
  3.1) repository=sarge ;;
  7.04*) repository=feisty ;;
  7.10*) repository=gutsy ;;
  8.04*|hardy) repository=hardy ;;
  8.10*|intrepid) repository=intrepid ;;
  *) echo "Couldn't guess your platform, giving up" ; exit 1 ;;
esac

echo $repository
