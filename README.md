Pogo - A simple and fast audio player for Linux
===============================================

Pogo plays your music. Nothing else. It is both fast and easy-to-use.
The clear interface uses the screen real-estate very efficiently. Other
features include: Fast search on the harddrive and in the playlist,
smart album grouping, cover display, desktop notifications and no music
library.

Pogo is a fork of Decibel Audio Player and supports most common audio
formats. It is written in Python and uses GTK+ and gstreamer.

To report bugs, suggest features, ask questions, get the latest version
or help out, visit http://launchpad.net/pogo.


Run Pogo without installing
===========================

    git clone https://github.com/jendrikseipp/pogo.git
    cd pogo
    ./pogo.py


Install and run Pogo
====================

    sudo apt-get install gettext python-mutagen python-gst0.10 python-dbus python-imaging
    sudo make install
    pogo


Requirements
============

Pogo depends on the Python runtime and the following libraries:

  * Python (>= 2.5):      http://www.python.org
  * PyGTK (>= 2.12):      http://www.pygtk.org
  * PyGST (>= 0.10.2):    http://gstreamer.freedesktop.org/
  * Mutagen (>= 1.10):    http://code.google.com/p/mutagen/
  * Python DBus:          http://dbus.freedesktop.org/
  * Python Imaging (PIL): http://www.pythonware.com/products/pil/

Recommended libraries (it is likely that they are already installed):

  * python-notify         (Nice notifications)
  * gnome-settings-daemon (GNOME media keys)

Particular audio formats depend on various GStreamer decoding elements,
as well as other Python modules. GStreamer splits their downlads into
good, bad, ugly, and ffmpeg packages, each of which contains elements;
you probably want them all.
