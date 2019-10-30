FROM debian:buster-slim
LABEL maintainer="Sebastien Delafond <sdelafond@gmail.com>"

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN echo 'APT::Install-Recommends "false";' > /etc/apt/apt.conf.d/no-recommends && \
    echo 'APT::Install-Suggests "false";' >> /etc/apt/apt.conf.d/no-recommends

RUN apt update -q

RUN apt install -y git
RUN apt install -y ca-certificates

# cleanup
RUN apt clean
RUN rm -rf /var/lib/apt/lists/*

# base dir
ENV UNTANGLE=/opt/untangle
RUN mkdir -p ${UNTANGLE}

# pkgtools
ENV PKGTOOLS=${UNTANGLE}/ngfw_pkgtools
COPY . ${PKGTOOLS}/

WORKDIR ${PKGTOOLS}

VOLUME ${PKGTOOLS}
