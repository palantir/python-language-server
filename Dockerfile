FROM python:3.7.10-buster

RUN apt-get update
RUN apt-get install -y nginx
RUN apt-get install -y lsof

RUN pip install tornado pyflakes jedi requests beautifulsoup4
RUN pip install -U python-jsonrpc-server
RUN pip install git+https://github.com/NapkinHQ/python-language-server.git

ARG github_token

RUN pip install git+https://${github_token}@github.com/NapkinHQ/pynapkin.git

# clone and install pyls fork
WORKDIR /napkin-ls

RUN ulimit -n 500000
#ADD server.py .
ADD server_test.py ./server.py
ADD nginx_default /etc/nginx/sites-available/default


ENTRYPOINT ["/bin/bash", "-c", "nginx; ./server.py"]