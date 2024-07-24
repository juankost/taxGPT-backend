FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY . /workspace/src
WORKDIR /workspace/src

RUN python3 -m pip install --no-cache-dir -e . 

RUN chmod +x /workspace/src/startup.sh
CMD ["/bin/bash", "/workspace/src/startup.sh"]