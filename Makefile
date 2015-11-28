test: vim-themis
	vim-themis/bin/themis --reporter spec test
	./run_tests.sh

# Use existing vim-themis install from ~/.vim, or clone it.
vim-themis:
	existing=$(firstword $(wildcard ~/.vim/*bundle*/*themis*/plugin/themis.vim)); \
	if [ -n "$$existing" ]; then \
		( cd test && ln -s $$(dirname $$(dirname $$existing)) vim-themis ); \
	else \
		git clone https://github.com/thinca/vim-themis vim-themis; \
	fi

.PHONY: test
