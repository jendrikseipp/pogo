#!/bin/sh

set -e

# if credentials are missing run:
# manage-credentials create -c ubuntu-dev-tools -l 2

VERSION=`python -c "import sys; sys.path.append('src/tools'); import consts; print consts.appVersion"`
./doc/create-releasenotes.py
lp-project-upload pogo $VERSION "pogo-$VERSION.tar.gz" $VERSION /dev/null RELEASENOTES
