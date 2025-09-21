IMAGE_NAME := joon78/minilm
TAG := latest

.PHONY: all build push

all: push

build:
	docker buildx build --platform linux/arm64 -t $(IMAGE_NAME):$(TAG) .

push: build
	docker push $(IMAGE_NAME):$(TAG)
