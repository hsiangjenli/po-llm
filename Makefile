.PHONY: setup

setup:
	sh bin/install_rye.sh

build:
	rye build

tag:
	sh bin/git_tag.sh

clean:
	rm -rf dist/
