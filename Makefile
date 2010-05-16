INSTALL ?= install
MAKE ?= make
RM ?= rm
RMDIR ?= rmdir
prefix ?= /usr/local


PREFIX = $(DESTDIR)$(prefix)

BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1
DATADIR = $(PREFIX)/share/decibel-audio-player
SRCDIR = $(DATADIR)/src
PIXDIR = $(DATADIR)/pix
RESDIR = $(DATADIR)/res

APPDIR = $(PREFIX)/share/applications
ICONDIR = $(PREFIX)/share/pixmaps
LOCALEDIR = $(PREFIX)/share/locale

CONFIGURE_IN = sed -e 's!prefix!$(prefix)!g'

LANGUAGES = `find locale/ -maxdepth 1 -mindepth 1 -type d -printf "%f "`

help:
	@echo Usage:
	@echo "make		- not used"
	@echo "make clean	- removes temporary data"
	@echo "make install	- installs data"
	@echo "make uninstall	- uninstalls data"
	@echo "make help	- prints this help"
	@echo


install:
	cat start.sh | $(CONFIGURE_IN) > decibel-audio-player;
	cat start-remote.sh | $(CONFIGURE_IN) > decibel-audio-player-remote;
	echo $(PREFIX)
	$(INSTALL) -m 755 -d $(BINDIR) $(MANDIR) $(DATADIR) $(SRCDIR) $(RESDIR) $(APPDIR) $(PIXDIR) $(ICONDIR)
	$(INSTALL) -m 755 -d $(SRCDIR)/gui
	$(INSTALL) -m 755 -d $(SRCDIR)/media
	$(INSTALL) -m 755 -d $(SRCDIR)/media/format
	$(INSTALL) -m 755 -d $(SRCDIR)/media/track
	$(INSTALL) -m 755 -d $(SRCDIR)/tools
	$(INSTALL) -m 755 -d $(SRCDIR)/modules
	$(INSTALL) -m 644 src/*.py $(SRCDIR)
	$(INSTALL) -m 644 src/gui/*.py $(SRCDIR)/gui
	$(INSTALL) -m 644 src/tools/*.py $(SRCDIR)/tools
	$(INSTALL) -m 644 src/media/*.py $(SRCDIR)/media
	$(INSTALL) -m 644 src/media/track/*.py $(SRCDIR)/media/track
	$(INSTALL) -m 644 src/media/format/*.py $(SRCDIR)/media/format
	$(INSTALL) -m 644 src/modules/*.py $(SRCDIR)/modules
	$(INSTALL) -m 644 res/*.glade $(RESDIR)
	$(INSTALL) -m 644 doc/decibel-audio-player.1 $(MANDIR)
	$(INSTALL) -m 644 doc/decibel-audio-player-remote.1 $(MANDIR)
	$(INSTALL) -m 644 pix/*.png $(PIXDIR)
	$(INSTALL) -m 644 pix/decibel-audio-player.png $(ICONDIR)
	$(INSTALL) -m 644 res/decibel-audio-player.desktop $(APPDIR)
	if test -L $(BINDIR)/decibel-audio-player; then ${RM} $(BINDIR)/decibel-audio-player; fi
	$(INSTALL) -m 755 decibel-audio-player $(BINDIR)
	if test -L $(BINDIR)/decibel-audio-player-remote; then ${RM} $(BINDIR)/decibel-audio-player-remote; fi
	$(INSTALL) -m 755 decibel-audio-player-remote $(BINDIR)
	$(MAKE) -C po dist
	for lang in $(LANGUAGES); do \
		${INSTALL} -m 755 -d $(LOCALEDIR)/$$lang/LC_MESSAGES;\
		$(INSTALL) -m 644 locale/$$lang/LC_MESSAGES/decibel-audio-player.mo $(LOCALEDIR)/$$lang/LC_MESSAGES/; \
	done


uninstall:
	${RM} $(BINDIR)/decibel-audio-player
	${RM} $(BINDIR)/decibel-audio-player-remote
	${RM} $(APPDIR)/decibel-audio-player.desktop
	${RM} $(MANDIR)/decibel-audio-player.1
	${RM} $(MANDIR)/decibel-audio-player-remote.1
	${RM} $(ICONDIR)/decibel-audio-player.png
	${RM} -rf $(DATADIR)
	$(RMDIR) --ignore-fail-on-non-empty $(BINDIR) $(MANDIR) $(APPDIR)
	for lang in $(LANGUAGES); do \
		${RM} $(LOCALEDIR)/$$lang/LC_MESSAGES/decibel-audio-player.mo; \
	done

clean:
	$(MAKE) -C po clean
	${RM} src/*.py[co] res/*~ res/*.bak
	${RM} decibel-audio-player decibel-audio-player-remote

.PHONY: help clean install
