#!/bin/sh

INSTALL_DIR="/usr/share/decibel-audio-player"
MAN_DIR="/usr/share/man/man1"
BIN_DIR="/usr/bin"
APP_DIR="/usr/share/applications"
LOC_DIR="/usr/share/locale"
ICO_DIR="/usr/local/share/pixmaps"
VERSION=`cat control-install | grep "Version" | cut -d\  -f2`

# Make clean
find -type f -name "*.pyc" -exec rm -f {} \;
find -type f -name "*.pyo" -exec rm -f {} \;

mkdir -p decibel-audio-player/DEBIAN
cp control-install decibel-audio-player/DEBIAN/control

mkdir -p "decibel-audio-player"$ICO_DIR
cp pix/decibel-audio-player.png "decibel-audio-player"$ICO_DIR

mkdir -p "decibel-audio-player"$MAN_DIR
cp doc/decibel-audio-player.1 "decibel-audio-player"$MAN_DIR
cp doc/decibel-audio-player-remote.1 "decibel-audio-player"$MAN_DIR

mkdir -p "decibel-audio-player"$INSTALL_DIR

cp -R src "decibel-audio-player"$INSTALL_DIR"/"

# Resources
mkdir -p "decibel-audio-player"$INSTALL_DIR"/res"
cd res
./optiglade.py
cd ..
cp res/*.glade "decibel-audio-player"$INSTALL_DIR"/res/"

mkdir -p "decibel-audio-player"$INSTALL_DIR"/pix"
cp pix/*.png "decibel-audio-player"$INSTALL_DIR"/pix/"

mkdir -p "decibel-audio-player"$INSTALL_DIR"/doc"
cp doc/LICENCE "decibel-audio-player"$INSTALL_DIR"/doc/"
cp doc/ChangeLog "decibel-audio-player"$INSTALL_DIR"/doc/"

mkdir -p "decibel-audio-player"$APP_DIR
cp res/*.desktop "decibel-audio-player"$APP_DIR

mkdir -p "decibel-audio-player"$BIN_DIR
cp start-package.sh "decibel-audio-player"$BIN_DIR"/decibel-audio-player"
cp start-remote-package.sh "decibel-audio-player"$BIN_DIR"/decibel-audio-player-remote"

# Create locales
rm -rf locale
cd po
make dist
cd ..

# Copy locales
mkdir -p "decibel-audio-player"$LOC_DIR
cp -R locale/* "decibel-audio-player"$LOC_DIR

# Remove .svn directories
find "decibel-audio-player" -type d -name ".svn" -exec rm -rf {} \; > /dev/null 2>&1

# Sources: Make sure to remove non-Python files
find "decibel-audio-player"$INSTALL_DIR"/src" -type f ! -name "*.py" -exec rm -f {} \;

dpkg-deb --build decibel-audio-player decibel-audio-player-$VERSION.deb
rm -rf decibel-audio-player
