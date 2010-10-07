INSTALL ?= install

PYFILES = $(shell find ../src -type f -name "*.py")
GLADEFILES = $(wildcard ../res/*.glade)
POFILES = $(wildcard *.po)

GLADEHFILES := $(GLADEFILES:.glade=.glade.h)

help:
	@echo USAGE:
	@echo "make update - updates pogo.pot and .po files"
	@echo "make dist   - creates .mo files in ../locale dir"
	@echo "make pl.po  - updates pl.po file OR creates new one"
	@echo "              (replace 'pl' with your language code)"

%.h: %
	intltool-extract --type="gettext/glade" $*
	sed -i '/^char \*s = N_("gtk-.*");$$/d' $@


pogo.pot: $(GLADEHFILES) $(PYFILES)
	xgettext -k_ -kN_ -o pogo.pot $(PYFILES) $(GLADEHFILES) --from-code=utf-8

%.po: pogo.pot
	@if test -f $@; then \
		echo -n "Updating '$*' language ";\
		msgmerge -U $@ pogo.pot;\
	else \
		msginit -l $*.UTF8 -o $@; \
	fi

%.mo:
	for pofile in $(patsubst ../locale/%/LC_MESSAGES/pogo.mo,%.po,$@); do \
		${INSTALL} -m 755 -d $(subst pogo.mo,,$@);\
		msgconv -t UTF-8 $${pofile} -o $${pofile}_utf8;\
		msgfmt $${pofile}_utf8 -o $@;\
		rm $${pofile}_utf8;\
	done

update: $(POFILES)
dist: $(POFILES:%.po=../locale/%/LC_MESSAGES/pogo.mo)

clean:
	$(RM) $(GLADEHFILES)
	$(RM) $(POFILES:%.po=../locale/%/LC_MESSAGES/pogo.mo)
	#$(RM) pogo.pot

.PHONY:  update
