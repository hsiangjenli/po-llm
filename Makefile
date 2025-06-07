.PHONY: setup

setup:
	sh bin/install_rye.sh

build:
	rye build

tag:
	sh bin/git_tag.sh

clean:
	rm -rf dist/

docker:
	docker buildx build --platform linux/amd64,linux/arm64 -t hsiangjenli/pollm:latest -f Dockerfile.sphinx --push .
