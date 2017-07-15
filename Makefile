INSTALL ?= install
MAKE ?= make
RM ?= rm
RMDIR ?= rmdir
prefix ?= /usr


PREFIX = $(DESTDIR)$(prefix)

BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1
DATADIR = $(PREFIX)/share/pogo
SRCDIR = $(DATADIR)/pogo
PIXDIR = $(DATADIR)/pix
RESDIR = $(DATADIR)/res

APPDIR = $(PREFIX)/share/applications
ICONDIR = $(PREFIX)/share/pixmaps
LOCALEDIR = $(PREFIX)/share/locale

CONFIGURE_IN = sed -e "s!prefix = '/usr'!prefix = '$(prefix)'!g"

LANGUAGES = `find locale/ -maxdepth 1 -mindepth 1 -type d -printf "%f "`

help:
	@echo Usage:
	@echo "make           - not used"
	@echo "make clean     - removes temporary data"
	@echo "make install   - installs data"
	@echo "make uninstall - uninstalls data"
	@echo "make test      - runs tests"
	@echo "make help      - prints this help"
	@echo

install:
	cat pogo.py | $(CONFIGURE_IN) > script;
	echo $(PREFIX)
	$(INSTALL) -m 755 -d $(BINDIR) $(MANDIR) $(DATADIR) $(SRCDIR) $(RESDIR) $(APPDIR) $(PIXDIR) $(ICONDIR)
	$(INSTALL) -m 755 -d $(SRCDIR)/gui
	$(INSTALL) -m 755 -d $(SRCDIR)/media
	$(INSTALL) -m 755 -d $(SRCDIR)/media/format
	$(INSTALL) -m 755 -d $(SRCDIR)/media/track
	$(INSTALL) -m 755 -d $(SRCDIR)/tools
	$(INSTALL) -m 755 -d $(SRCDIR)/modules
	$(INSTALL) -m 644 pogo/*.py $(SRCDIR)
	$(INSTALL) -m 644 pogo/gui/*.py $(SRCDIR)/gui
	$(INSTALL) -m 644 pogo/tools/*.py $(SRCDIR)/tools
	$(INSTALL) -m 644 pogo/media/*.py $(SRCDIR)/media
	$(INSTALL) -m 644 pogo/media/track/*.py $(SRCDIR)/media/track
	$(INSTALL) -m 644 pogo/media/format/*.py $(SRCDIR)/media/format
	$(INSTALL) -m 644 pogo/modules/*.py $(SRCDIR)/modules
	$(INSTALL) -m 644 res/*.ui $(RESDIR)
	$(INSTALL) -m 644 res/pogo.1 $(MANDIR)
	$(INSTALL) -m 644 pix/*.png $(PIXDIR)
	$(INSTALL) -m 644 pix/pogo.png $(ICONDIR)
	$(INSTALL) -m 644 res/pogo.desktop $(APPDIR)
	if test -L $(BINDIR)/pogo; then ${RM} $(BINDIR)/pogo; fi
	$(INSTALL) -m 755 script $(BINDIR)/pogo
	$(MAKE) -C po dist
	for lang in $(LANGUAGES); do \
		${INSTALL} -m 755 -d $(LOCALEDIR)/$$lang/LC_MESSAGES;\
		$(INSTALL) -m 644 locale/$$lang/LC_MESSAGES/pogo.mo $(LOCALEDIR)/$$lang/LC_MESSAGES/; \
	done

uninstall:
	${RM} $(BINDIR)/pogo
	${RM} $(APPDIR)/pogo.desktop
	${RM} $(MANDIR)/pogo.1
	${RM} $(ICONDIR)/pogo.png
	${RM} -rf $(DATADIR)
	$(RMDIR) --ignore-fail-on-non-empty $(BINDIR) $(MANDIR) $(APPDIR)
	for lang in $(LANGUAGES); do \
		${RM} $(LOCALEDIR)/$$lang/LC_MESSAGES/pogo.mo; \
	done

clean:
	$(MAKE) -C po clean
	${RM} pogo/*.py[co] res/*~ res/*.bak
	${RM} script

test:
	pyflakes pogo pogo.py

.PHONY: help clean install test
