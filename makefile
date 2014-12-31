TARGET=protokoll
###
### generic GNU make Makefile for .tex -> .pdf.
### ransford at cs.washington.edu
###   http://github.com/ransford/pdflatex-makefile
###
### Recommended usage:
###   1. echo 'include Makefile.include' > Makefile
###   2. Optional: Edit the Makefile to override $(TARGET)
###      and anything else (e.g., PDFVIEWER, AFTERALL)
###
### Final result:
###   % cat Makefile
###   TARGET=mypaper
###   PDFVIEWER=open -a 'Adobe Acrobat Professional'
###   AFTERALL=mypostprocessingstep
###   include Makefile.include
###
###   mypostprocessingstep:
###           # do something...
###

PDFLATEX	?= pdflatex -halt-on-error -file-line-error
BIBTEX		 = bibtex

ifneq ($(QUIET),)
PDFLATEX	+= -interaction=batchmode
ERRFILTER	:= > /dev/null || (egrep ':[[:digit:]]+:' *.log && false)
BIBTEX		+= -terse
else
PDFLATEX	+= -interaction=nonstopmode
ERRFILTER=
endif

## Action for 'make view'
OS=$(shell uname -s)
ifeq ($(OS),Darwin)
PDFVIEWER	?= open
else
PDFVIEWER	?= xdg-open
endif

RM = rm -rf

## Name of the target file, minus .pdf: e.g., TARGET=mypaper causes this
## Makefile to turn mypaper.tex into mypaper.pdf.
TARGETS += $(TARGET)
TEXTARGETS = $(TARGETS:=.tex)
PDFTARGETS = $(TARGETS:=.pdf)
AUXFILES   = $(TARGETS:=.aux)
LOGFILES   = $(TARGETS:=.log)

## Inkscape svg handling
INKSCAPE	?= /usr/bin/inkscape
INKSCAPE_ARGS ?= --export-latex --export-area-page
SVGDIR		?= svg
SVGFILES	?= $(basename $(notdir $(wildcard $(SVGDIR)/*.svg)))

BIBLATEX	?= $(shell grep -o '^[^%]*\\usepackage[^{]*{biblatex}' $(TEXTARGETS) \
					| grep -o 'backend=\(biber\|bibtex\)' \
					| sed -e 's/backend=//')
BIBTEX = $(BIBLATEX)

## If $(TARGET).tex refers to .bib files like \bibliography{foo,bar}, then
## $(BIBFILES) will contain foo.bib and bar.bib, and both files will be added as
## dependencies to $(PDFTARGETS).
## Effect: updating a .bib file will trigger re-typesetting.
BIBFILES = $(addsuffix .bib,\
		$(shell grep '^[^%]*\\bibliography{' $(TEXTARGETS) | \
			grep -o '\\bibliography{[^}]\+}' | \
			sed -e 's/^[^%]*\\bibliography{\([^}]*\)}.*/\1/' \
				-e 's/, */ /g'))

ifneq ($(BIBLATEX),) # BibLaTeX not empty
	BIBFILES += $(shell grep '^[^%]*\\addbibresource{' $(TEXTARGETS) | \
			grep -o '\\addbibresource{[^}]\+}' | \
			sed -e 's/^[^%]*\\addbibresource{\([^}]*\)}.*/\1/' \
				-e 's/, */ /g')
endif

## Add \input'ed or \include'd files to $(PDFTARGETS) dependencies.
INCLUDEDTEX = $(addsuffix .tex,\
		$(shell grep '^[^%]*\\\(input\|include\){' $(TEXTARGETS) | \
			grep -o '\\\(input\|include\){[^}]\+}' | \
			sed -e 's/^.*{\([^}]*\)}.*/\1/' | \
			grep -v '^img-.*pdf_tex$$'))

AUXFILES += $(INCLUDEDTEX:.tex=.aux)

## grab a version number from the repository (if any) that stores this.
## * REVISION is the current revision number (short form, for inclusion in text)
## * VCSTURD is a file that gets touched after a repo update
SPACE = $(empty) $(empty)
ifeq ($(shell git status >/dev/null 2>&1 && echo USING_GIT),USING_GIT)
  ifeq ($(shell git svn info >/dev/null 2>&1 && echo USING_GIT_SVN),USING_GIT_SVN)
    # git-svn
    REVISION := $(shell git svn find-rev git-svn)
    VCSTURD := $(subst $(SPACE),\ ,$(shell git rev-parse --show-toplevel)/.git/refs/remotes/git-svn)
  else
    # plain git
    REVISION := $(shell git rev-parse --short HEAD)
    GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null)
    VCSTURD := $(subst $(SPACE),\ ,$(shell git rev-parse --show-toplevel)/.git/$(GIT_BRANCH))
  endif
else ifeq ($(shell hg root >/dev/null 2>&1 && echo USING_HG),USING_HG)
  # mercurial
  REVISION := $(shell hg id -i)
  VCSTURD := $(subst $(SPACE),\ ,$(shell hg root)/.hg/dirstate)
else ifneq ($(wildcard .svn/entries),)
  # subversion
  REVISION := $(subst :,-,$(shell svnversion -n))
  VCSTURD := .svn/entries
endif

# enable PythonTeX-Support?
PYTHONTEX	= $(shell grep -o '^[^%]*\\usepackage[^{]*{pythontex}' $(TEXTARGETS))
ifneq ($(PYTHONTEX),)
  PYTHONTEXFILES = $(addprefix pythontex-files-,$(TARGETS))
else
  PYTHONTEXFILES = $(empty)
endif

# .PHONY names all targets that aren't filenames
.PHONY: all clean pdf view snapshot distill clean-all

all: pdf $(AFTERALL)

pdf: $(PDFTARGETS)

view: $(PDFTARGETS)
	$(PDFVIEWER) $(PDFTARGETS)

# define a \Revision{} command you can include in your document's preamble.
# especially useful with e.g. draftfooter.sty or fancyhdr.
# usage: \input{revision}
#        ... \Revision{}
ifneq ($(REVISION),)
REVDEPS += revision.tex
revision.tex: $(VCSTURD)
	/bin/echo '\newcommand{\Revision}'"{$(REVISION)}" > $@
AUXFILES += revision.aux
endif

# to generate aux but not pdf from pdflatex, use -draftmode
.INTERMEDIATE: $(AUXFILES)
%.aux %.bbl %.pytxcode: %.tex $(REVDEPS) $(BIBFILES)
	$(PDFLATEX) -draftmode $* $(ERRFILTER)

# introduce BibTeX dependency if we found a \bibliography
ifneq ($(strip $(BIBFILES)),)
BIBDEPS = %.bbl
ifneq ($(BIBLATEX),)
%.bbl: %.bcf $(BIBFILES)
	$(BIBLATEX) $*
else
%.bbl: %.aux $(BIBFILES)
	$(BIBTEX) $*
endif
endif

ifneq ($(PYTHONTEX),)
pythontex-files-%: %.pytxcode
	pythontex $*
endif

$(PDFTARGETS): %.pdf: %.tex $(addsuffix .pdf,$(addprefix img-,$(SVGFILES))) %.aux $(PYTHONTEXFILES) $(BIBDEPS) $(INCLUDEDTEX) $(REVDEPS)
	$(PDFLATEX) $* $(ERRFILTER)
ifneq ($(strip $(BIBFILES)),)
	@if grep -q "undefined references" $*.log; then \
		$(BIBTEX) $* && $(PDFLATEX) $* $(ERRFILTER); fi
endif
	@while grep -q "Rerun to" $*.log; do \
		$(PDFLATEX) $* $(ERRFILTER); done

img-%.pdf: $(SVGDIR)/%.svg
	$(INKSCAPE) $(INKSCAPE_ARGS) --file=$< --export-pdf=$@

DRAFTS := $(PDFTARGETS:.pdf=-$(REVISION).pdf)
$(DRAFTS): %-$(REVISION).pdf: %.pdf
	cp $< $@
snapshot: $(DRAFTS)

%.distilled.pdf: %.pdf
	gs -q -dSAFER -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$@ \
		-dCompatibilityLevel=1.5 -dPDFSETTINGS=/prepress -c .setpdfwrite -f $<
	exiftool -overwrite_original -Title="" -Creator="" -CreatorTool="" $@

distill: $(PDFTARGETS:.pdf=.distilled.pdf)

clean-all: clean
	$(RM) $(PDFTARGETS) $(PDFTARGETS:.pdf=.distilled.pdf) $(EXTRADISTCLEAN)

clean:
	$(RM) $(foreach T,$(TARGETS), $(T).out $(T).blg $(T).bbl $(T).lof $(T).lot $(T).toc $(T).idx $(T).nav $(T).snm $(T).bcf $(T).run.xml $(T).pytxcode pythontex-files-$(T)) $(foreach S,$(addprefix img-,$(SVGFILES)),$(S).pdf $(S).pdf_tex) $(REVDEPS) $(AUXFILES) $(LOGFILES) $(EXTRACLEAN)
