MININET = nestnet/*.py
TEST = nestnet/test/*.py
EXAMPLES = nestnet/examples/*.py
MN = bin/nn
PYTHON ?= python3
PYMN = $(PYTHON) -B bin/nn
BIN = $(MN)
PYSRC = $(MININET) $(TEST) $(EXAMPLES) $(BIN)
MNEXEC = nnexec
MANPAGES = nn.1 nnexec.1
P8IGN = E251,E201,E302,E202,E126,E127,E203,E226
PREFIX ?= /usr
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/share/man/man1
DOCDIRS = doc/html doc/latex
PDF = doc/latex/refman.pdf

CFLAGS += -Wall -Wextra

all: test

clean:
	rm -rf build dist *.egg-info *.pyc $(MNEXEC) $(MANPAGES) $(DOCDIRS)

test: $(MININET) $(TEST)
	-echo "Running tests"
	py.test -v nestnet/test/test_containernet.py

nnexec: nnexec.c $(MN) nestnet/net.py
	cc $(CFLAGS) $(LDFLAGS) -DVERSION=\"`PYTHONPATH=. $(PYMN) --version`\" $< -o $@

install-nnexec: $(MNEXEC)
	install -D $(MNEXEC) $(BINDIR)/$(MNEXEC)

install-manpages: $(MANPAGES)
	install -D -t $(MANDIR) $(MANPAGES)

install: install-nnexec install-manpages
	$(PYTHON) setup.py install

develop: $(MNEXEC) $(MANPAGES)
# 	Perhaps we should link these as well
	install $(MNEXEC) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	$(PYTHON) setup.py develop

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
