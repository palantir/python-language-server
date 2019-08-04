FROM python:3.6-slim
# Install pyls
RUN pip install python-language-server
# Run the LSP on port 5007
ENTRYPOINT ["pyls", "--tcp", "--port", "5007", "--host", "0.0.0.0"]
