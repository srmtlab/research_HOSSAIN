all:
	platex main.tex
	pbibtex main
	platex main.tex
	platex main.tex
	dvipdfmx main.dvi

view:
	okular paper.pdf

clean:
	find ./ -name "*.aux" | xargs rm -rf
	find ./ -name "*.bbl" | xargs rm -rf
	find ./ -name "*.blg" | xargs rm -rf
	find ./ -name "*.out" | xargs rm -rf
	find ./ -name "*.log" | xargs rm -rf