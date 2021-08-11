NESTNET = nestnet/*.py
TEST = nestnet/test/*.py
EXAMPLES = nestnet/examples/*.py
MN = bin/nn
PYTHON ?= python
PYMN = $(PYTHON) -B bin/nn
BIN = $(MN)
PYSRC = $(NESTNET) $(TEST) $(EXAMPLES) $(BIN)
MNEXEC = nnexec
MANPAGES = nn.1 nnexec.1
P8IGN = E251,E201,E302,E202,E126,E127,E203,E226,E402,W504,W503,E731
PREFIX ?= /usr
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/share/man/man1
DOCDIRS = doc/html doc/latex
PDF = doc/latex/refman.pdf
CC ?= cc

CFLAGS += -Wall -Wextra

all: codecheck test

clean:
	rm -rf build dist *.egg-info *.pyc $(MNEXEC) $(MANPAGES) $(DOCDIRS)

codecheck: $(PYSRC)
	-echo "Running code check"
	util/versioncheck.py
	pyflakes $(PYSRC)
	pylint --rcfile=.pylint $(PYSRC)
#	Exclude miniedit from pep8 checking for now
	pep8 --repeat --ignore=$(P8IGN) `ls $(PYSRC) | grep -v miniedit.py`

errcheck: $(PYSRC)
	-echo "Running check for errors only"
	pyflakes $(PYSRC)
	pylint -E --rcfile=.pylint $(PYSRC)

test: $(NESTNET) $(TEST)
	-echo "Running tests"
	nestnet/test/test_nets.py
	nestnet/test/test_hifi.py

slowtest: $(NESTNET)
	-echo "Running slower tests (walkthrough, examples)"
	nestnet/test/test_walkthrough.py -v
	nestnet/examples/test/runner.py -v

nnexec: nnexec.c $(MN) nestnet/net.py
	$(CC) $(CFLAGS) $(LDFLAGS) \
	-DVERSION=\"`PYTHONPATH=. $(PYMN) --version 2>&1`\" $< -o $@

install-nnexec: $(MNEXEC)
	install -D $(MNEXEC) $(BINDIR)/$(MNEXEC)

install-manpages: $(MANPAGES)
	install -D -t $(MANDIR) $(MANPAGES)

install: install-nnexec install-manpages
#	This seems to work on all pip versions
	$(PYTHON) -m pip uninstall -y nestnet || true
	$(PYTHON) -m pip install .

develop: $(MNEXEC) $(MANPAGES)
# 	Perhaps we should link these as well
	install $(MNEXEC) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	$(PYTHON) -m pip uninstall -y nestnet || true
	$(PYTHON) -m pip install -e . --no-binary :all:

man: $(MANPAGES)

nn.1: $(MN)
	PYTHONPATH=. help2man -N -n "create a Mininet network." \
	--no-discard-stderr "$(PYMN)" -o $@

nnexec.1: nnexec
	help2man -N -n "execution utility for Mininet." \
	-h "-h" -v "-v" --no-discard-stderr ./$< -o $@

.PHONY: doc

doc: man
	doxygen doc/doxygen.cfg
	make -C doc/latex
