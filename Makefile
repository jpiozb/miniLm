IMAGE_NAME := joon78/minilm
TAG := latest

.PHONY: update-embeddings docker

docker:
	docker buildx build --no-cache --platform linux/arm64 -t $(IMAGE_NAME):$(TAG) . --push

update-embeddings:
	.venv/bin/python3 app.py