FROM python:3.6.13-buster


RUN pip install tornado pyflakes jedi requests beautifulsoup4
RUN pip install -U python-jsonrpc-server
RUN pip install git+https://github.com/NapkinHQ/python-language-server.git

ARG github_token

RUN pip install git+https://${github_token}@github.com/NapkinHQ/pynapkin.git

RUN apt-get update && apt-get install -y nginx lsof

# clone and install pyls fork
WORKDIR /napkin-ls

RUN ulimit -n 500000
#ADD server.py .
ADD server_test.py ./server.py
ADD nginx_default /etc/nginx/sites-available/default


ENTRYPOINT ["/bin/bash", "-c", "nginx; ./server.py"]