Pogo - A fast and minimalist audio player for Linux
===================================================

It groups tracks by album, which uses less space and simplifies
rearranging your playlist. Pogo does not organize your tracks in a music
library and does not stream or download tracks. Therefore, it is best
suited for people who store their tracks by album and want a simple way
of playing them. Pogo allows you to quickly search for music on local
drives and in the playlist. It also features an equalizer and displays
covers and desktop notifications.

Pogo is a fork of Decibel Audio Player and supports most common audio
formats. It is written in Python and uses GTK+ and GStreamer.

To report bugs, suggest features or ask questions, please visit
http://launchpad.net/pogo.

![Pogo screenshot](https://www.dropbox.com/s/wm3xtnvorysmytc/pogo-0.1-1.png?raw=1)

Requirements
------------

See `debian/control` for Ubuntu package names.

  * Python (>= 3.2):        http://www.python.org
  * GTK+ (>= 3.0):          http://www.gtk.org
  * GStreamer (>= 1.0):     http://gstreamer.freedesktop.org/
  * Mutagen:                https://github.com/quodlibet/mutagen
  * Python DBus:            http://dbus.freedesktop.org/
  * Pillow:                 https://github.com/python-pillow/Pillow

Recommended libraries:

  * libnotify               (Desktop notifications)
  * GNOME settings daemon   (GNOME media keys)
  * GStreamer plugins       (Support for various audio formats)


Run Pogo (without installing)
-----------------------------

    ./pogo.py


Install and run Pogo
--------------------

    sudo make install
    pogo


Ubuntu packages
---------------

  * Stable: https://launchpad.net/~pogo-dev/+archive/ubuntu/stable
  * Daily builds: https://launchpad.net/~pogo-dev/+archive/ubuntu/daily


Participate
-----------

  * Issues: https://bugs.launchpad.net/pogo
  * Questions: https://answers.launchpad.net/pogo
  * Translations: https://translations.launchpad.net/pogo
