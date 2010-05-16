INSTALL ?= install

PYFILES = $(shell find ../src -type f -name "*.py")
GLADEFILES = $(wildcard ../res/*.glade)
POFILES = $(wildcard *.po)

GLADEHFILES := $(GLADEFILES:.glade=.glade.h)

help:
	@echo "USAGE:"
	@echo "make update - updates messages.pot and .po files"
	@echo "make dist   - creates .mo files in ../locale dir"
	@echo "make pl.po  - updates pl.po file OR creates new one"
	@echo "              (replace 'pl' with your language code)"

%.h: %
	intltool-extract --type="gettext/glade" $*
	sed -i '/^char \*s = N_("gtk-.*");$$/d' $@


messages.pot: $(GLADEHFILES) $(PYFILES)
	xgettext -k_ -kN_ -o messages.pot $(PYFILES) $(GLADEHFILES) --from-code=utf-8

%.po: messages.pot
	@if test -f $@; then \
		echo -n "Updating '$*' language ";\
		msgmerge -U $@ messages.pot;\
	else \
		msginit -l $*.UTF8 -o $@; \
	fi

%.mo:
	for pofile in $(patsubst ../locale/%/LC_MESSAGES/decibel-audio-player.mo,%.po,$@); do \
		${INSTALL} -m 755 -d $(subst decibel-audio-player.mo,,$@);\
		msgconv -t UTF-8 $${pofile} -o $${pofile}_utf8;\
		msgfmt $${pofile}_utf8 -o $@;\
		rm $${pofile}_utf8;\
	done

update: $(POFILES)
dist: $(POFILES:%.po=../locale/%/LC_MESSAGES/decibel-audio-player.mo)

clean:
	$(RM) $(GLADEHFILES)
	$(RM) $(POFILES:%.po=../locale/%/LC_MESSAGES/decibel-audio-player.mo)
	#$(RM) messages.pot

.PHONY:  update
