test: vim-themis
	vim-themis/bin/themis --reporter spec test
	nosetests -v rplugin/python3
	flake8 rplugin/
	mypy --silent-imports rplugin/python3/deoplete

# Use existing vim-themis install from ~/.vim, or clone it.
vim-themis:
	git clone https://github.com/thinca/vim-themis vim-themis; \

.PHONY: test
