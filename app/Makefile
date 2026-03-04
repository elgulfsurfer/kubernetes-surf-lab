REGISTRY := ghcr.io/elgulfsurfer/kubernetes-lab
VERSION  := $(shell cat VERSION)

.PHONY: build push run login bump

bump:
	@parts=$$(echo $(VERSION) | tr '.' ' '); \
	major=$$(echo $$parts | awk '{print $$1}'); \
	minor=$$(echo $$parts | awk '{print $$2}'); \
	patch=$$(echo $$parts | awk '{print $$3}'); \
	patch=$$((patch + 1)); \
	echo "$$major.$$minor.$$patch" > VERSION; \
	echo "Bumped to $$(cat VERSION)"

build:
	docker build \
		--platform linux/amd64 \
		--build-arg VERSION=$(VERSION) \
		-t $(REGISTRY):$(VERSION) \
		-t $(REGISTRY):latest \
		.

push:
	docker push $(REGISTRY):$(VERSION)
	docker push $(REGISTRY):latest

run:
	docker run --rm -p 8000:8000 $(REGISTRY):latest

login:
	docker login ghcr.io -u elgulfsurfer
