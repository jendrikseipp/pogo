Pogo - A simple and fast audio player for Linux
===============================================

Its clean interface makes Pogo a perfect fit for small screens. Other
features include: fast search on the harddrive and in the playlist,
smart album grouping, cover display, desktop notifications and the lack
of a music library.

Pogo is a fork of Decibel Audio Player and supports most common audio
formats. It is written in Python and uses GTK+ and GStreamer.

To report bugs, suggest features, ask questions, get the latest version
or help out, please visit http://launchpad.net/pogo.


Requirements
============

See `debian/control` for Ubuntu package names.

  * Python (>= 3.2):        http://www.python.org
  * GTK (>= 2.12):          http://www.gtk.org
  * GStreamer (>= 1.0):     http://gstreamer.freedesktop.org/
  * Mutagen:                https://github.com/quodlibet/mutagen
  * Python DBus:            http://dbus.freedesktop.org/
  * Pillow:                 https://github.com/python-pillow/Pillow

Recommended libraries:

  * libnotify               (Desktop notifications)
  * GNOME settings daemon   (GNOME media keys)
  * GStreamer plugins       (Support for various audio formats)


Run Pogo (without installing)
=============================

    ./pogo.py


Install and run Pogo
====================

    sudo make install
    pogo



