#TEXFILE=conference_101719
TEXFILE=kiplot
#TEXFILE=rebuttal_y_trabajo
PS2PDF_OPTS=-sPAPESIZE=a4 -dPDFSETTINGS=/printer -dMaxSubsetPct=100 -dSubsetFont
s=true -dEmbedAllFonts=true

help:
	@echo "Targets importantes:"
	@echo "      dvi: General el .dvi"
	@echo "      pdf: General el .pdf"
	@echo "       ps: General el .ps"
	@echo "     vpdf: Visualiza el .pdf"
	@echo "     vdvi: Visualiza el .dvi"
	@echo "      vps: Visualiza el .ps"
	@echo "      eps: Genera las imágenes .eps"
	@echo " cleaneps: Borra las imágenes .eps"
	@echo "    clean: Borra los derivados del LaTeX"
	@echo " cleanall: Borra todo"
	@echo "NOTA: la generación de imágenes eps es independiente "
	@echo "(y previa) de la generación del documento LaTeX."
	@echo "Es decir: 'make eps' primero y luego 'make vpdf' x ejemplo."

all: $(TEXFILE).dvi

pdf : $(TEXFILE).pdf

vpdf: $(TEXFILE).pdf
	xpdf $(TEXFILE).pdf&

vps: $(TEXFILE).ps
	gv $(TEXFILE).ps&

vdvi: $(TEXFILE).dvi
	xdvi $(TEXFILE).dvi&

$(TEXFILE).ps :  $(TEXFILE).dvi
	dvips  -t a4  $(TEXFILE).dvi

$(TEXFILE).pdf :  $(TEXFILE).ps
	ps2pdf   $(PS2PDF_OPTS)  $(TEXFILE).ps


$(TEXFILE).dvi :  $(TEXFILE).tex   utic.bib
	latex  $(TEXFILE).tex
	#makeindex $(TEXFILE).idx
	bibtex -terse $(TEXFILE).aux
	echo "SECONDRUN" 1>&2
	latex  $(TEXFILE).tex
	latex  $(TEXFILE).tex

aspell: $(TEXFILE).tex
	aspell -t --encoding=iso8859-1 -c $(TEXFILE).tex

force:
	touch $(TEXFILE).tex
	make

eps:
	make -C img eps

cleanall: clean cleaneps

cleaneps:
	make -C img clean

clean:
	@-rm  -f $(TEXFILE).dvi $(TEXFILE).pdf $(TEXFILE).log $(TEXFILE).toc 2>/dev/null
	@-rm  -f $(TEXFILE).aux $(TEXFILE).ps $(TEXFILE).bbl $(TEXFILE).blg  2>/dev/null
	@-rm  -f $(TEXFILE).lof $(TEXFILE).idx $(TEXFILE).ind $(TEXFILE).ilg 2>/dev/null
	@-rm  -f .firstrun  2>/dev/null
