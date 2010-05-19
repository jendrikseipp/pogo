#!/bin/sh

ARCHIVE=`date +%Y%m%d`"-decibel-audio-player.tar.bz2"
DEST='./Decibel-Audio-Player'

if [ -d $DEST ]; then
  rm -rf $DEST
fi

# Make clean
find -type f -name "*.pyc" -exec rm -f {} \;
find -type f -name "*.pyo" -exec rm -f {} \;

mkdir $DEST

# Sources
cp -R ./src/ $DEST/

# Images
cp -R ./pix/ $DEST/

# Resources
cd res
./optiglade.py
cd ..
mkdir $DEST/res/
cp res/*.py $DEST/res/
cp res/*.glade $DEST/res/
cp res/*.desktop $DEST/res/

# Locales
cp -R ./po/ $DEST/

# Benchmarks
cp -R benchmarks $DEST/

# Scripts
cp *.sh $DEST/

# Doc
cp -R ./doc/ $DEST/

# Misc
cp TODO control-install Makefile $DEST/

# Remove .svn and .bzr directories
cd $DEST
find -type d -name ".svn" -exec rm -rf {} \; > /dev/null 2>&1
find -type d -name ".bzr" -exec rm -rf {} \; > /dev/null 2>&1
cd ..

tar cjf $ARCHIVE $DEST
rm -rf $DEST
