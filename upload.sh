#!/bin/sh

set -e
set -u

# if credentials are missing run:
# manage-credentials create -c ubuntu-dev-tools -l 2

NEWS="$1"
TARBALL="pogo-$VERSION.tar.gz"

cd "$(dirname "$0")"

VERSION=`python -c "import sys; sys.path.append('src/tools'); import consts; print consts.appVersion"`
# Tool resides in package lptools.
lp-project-upload pogo $VERSION $TARBALL $VERSION /dev/null "$NEWS"

rm $TARBALL
rm $TARBALL.asc
