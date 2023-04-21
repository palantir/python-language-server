GITHUB_TOKEN ?= "stub"

build-local:
	docker build --file Dockerfile.local --build-arg github_token=${GITHUB_TOKEN} -t py-lang-server-local:latest .

run-local:
	docker run -it -p 3001:80 py-lang-server-local:latest

local: build run