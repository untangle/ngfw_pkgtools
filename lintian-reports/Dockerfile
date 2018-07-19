FROM debian:buster
LABEL maintainer="Sebastien Delafond <sdelafond@gmail.com>"

RUN echo 'APT::Install-Recommends "false";' > /etc/apt/apt.conf.d/00-no-recommends && \
    echo 'APT::Install-Suggests "false";' > /etc/apt/apt.conf.d/00-no-suggests

RUN apt-get update
RUN apt-get install -y gnuplot-nox
RUN apt-get install -y git
RUN apt-get install -y lintian
RUN apt-get install -y docbook-utils
RUN apt-get install -y fakeroot
RUN apt-get install -y debhelper
RUN apt-get install -y libtext-template-perl

WORKDIR /opt
RUN GIT_SSL_NO_VERIFY=1 git clone -b untangle https://github.com/sdelafond/lintian.git

WORKDIR /opt/lintian
RUN fakeroot debian/rules generate-docs

WORKDIR /opt
ADD config.yaml suppressed-tags.txt ./

VOLUME /var/www/lintian-reports
VOLUME /var/www/public/stretch

ENTRYPOINT [ "lintian/reporting/harness" ]
