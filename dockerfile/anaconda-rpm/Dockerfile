# This container is used for runing Anaconda RPM tests in the controlled environment.
# To find out how to build this container please look on the ./tests/README.rst file.

# The `image` arg will set base image for the build.
# possible values:
#   registry.fedoraproject.org/fedora:38
#   registry.fedoraproject.org/fedora:rawhide
#   registry-proxy.engineering.redhat.com/rh-osbs/ubi9:latest # private source
#   registry.access.redhat.com/ubi8/ubi # public source
ARG image
FROM ${image}
# FROM starts a new build stage with new ARGs. Put any ARGs after FROM unless required by the FROM itself.
# see https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact

# The `git_branch` arg will set git branch of Anaconda from which we are downloding spec file to get
# dependencies.
# possible values:
#   main
#   fedora-38
ARG git_branch
ARG copr_repo=@rhinstaller/Anaconda
LABEL maintainer=anaconda-devel@lists.fedoraproject.org

# The anaconda.spec.in is in the repository root. This file will be copied automatically here if
# the build is invoked by Makefile.
COPY ["anaconda.spec.in", "requirements.txt", "/root/"]

# Replace standalone systemd package with systemd as these are conflicting
RUN set -ex; \
    dnf install -y systemd --allowerasing

# Prepare environment and install build dependencies
RUN set -ex; \
  # disable fedora-cisco repository otherwise freerdp will depend on openh264 from fedora-cisco
  # if fedora-cisco is not enabled it will fallback to stub library in main repository which is
  # what we want
  sed -i 's/enabled=1/enabled=0/' /etc/yum.repos.d/fedora-cisco-openh264.repo; \
  dnf update -y; \
  # Install dependencies
  dnf install -y \
  'dnf5-command(copr)' \
  git \
  curl \
  python3-pip \
  python3-polib \
  /usr/bin/xargs \
  rsync \
  rpm-build \
  rpmlint; \
  if ! grep -q VARIANT.*eln /etc/os-release; then \
    BRANCH="${git_branch}"; \
    if [ $BRANCH == "main" ]; then \
      BRANCH="rawhide"; \
    fi; \
    BRANCH=${BRANCH#fedora-}; \
    dnf copr enable -y ${copr_repo} fedora-${BRANCH}-x86_64; \
    dnf copr enable -y @storage/blivet-daily fedora-${BRANCH}-x86_64; \
    dnf copr enable -y @storage/udisks-daily fedora-${BRANCH}-x86_64; \
  else \
    dnf copr enable -y ${copr_repo} fedora-eln-x86_64; \
  fi; \
  cat /root/anaconda.spec.in | sed 's/@PACKAGE_VERSION@/0/; s/@PACKAGE_RELEASE@/0/; s/%{__python3}/python3/' > /tmp/anaconda.spec; \
  rpmspec -q --buildrequires /tmp/anaconda.spec | xargs -d '\n' dnf install -y; \
  dnf clean all; \
  mkdir /anaconda

RUN pip install --no-cache-dir --upgrade pip; \
  pip install --no-cache-dir -r /root/requirements.txt

WORKDIR /anaconda
