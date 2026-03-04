REGISTRY := ghcr.io/elgulfsurfer/kubernetes-lab-resume-app

.PHONY: build push run login

build:
	docker build \
		-t $(REGISTRY):latest \
		.

push:
	docker push $(REGISTRY):latest

run:
	docker run --rm -p 8080:8080 \
		-v $(PWD)/resume.json:/etc/config/resume.json \
		$(REGISTRY):latest \
		--resume /etc/config/resume.json

login:
	docker login ghcr.io -u elgulfsurfer