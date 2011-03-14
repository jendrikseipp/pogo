#!/bin/sh

set -e

VERSION=`cat control-install | grep "Version" | cut -d\  -f2`
ARCHIVE="pogo-"$VERSION".tar.gz"
DEST='pogo-'$VERSION

if [ -d $DEST ]; then
  rm -rf $DEST
fi

mkdir $DEST

# Make clean
find -type f -name "*.pyc" -exec rm -f {} \;
find -type f -name "*.pyo" -exec rm -f {} \;

# Sources
cp -R ./src $DEST/

# Images
cp -R ./pix/ $DEST/

# Resources
mkdir $DEST/res/
cp ./res/*.glade $DEST/res/
cp ./res/*.desktop $DEST/res/

# Scripts
cp Makefile $DEST/
cp pogo.py $DEST/

# Doc
mkdir $DEST/doc
cp ./doc/COPYING $DEST/
cp ./doc/NEWS $DEST/
cp ./doc/README $DEST/

cp ./doc/pogo.1 $DEST/doc

# Locales
mkdir $DEST/po
cp ./po/*.po $DEST/po/
cp ./po/Makefile $DEST/po/

# Remove .svn and .bzr directories
find $DEST -type d -name ".svn" -exec rm -rf {} \; > /dev/null 2>&1
find $DEST -type d -name ".bzr" -exec rm -rf {} \; > /dev/null 2>&1

# Sources: Make sure to remove non-Python files
find $DEST/src -type f ! -name "*.py" -exec rm -f {} \;

tar czf $ARCHIVE $DEST
#rm -rf $DEST
