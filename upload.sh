#!/bin/sh

set -e

# if credentials are missing run:
# manage-credentials create -c ubuntu-dev-tools -l 2

VERSION=`cat control-install | grep "Version" | cut -d\  -f2`
lp-project-upload pogo $VERSION "pogo-$VERSION.tar.gz"
