ENV ?= dev
REGISTRY := 937976602373.dkr.ecr.us-east-2.amazonaws.com

build:
	docker build --file Dockerfile.local --build-arg github_token=${GITHUB_TOKEN} -t ${REGISTRY}/py-lang-server .

run:
	docker run -it -p 3001:80 ${REGISTRY}/py-lang-server

local: build run