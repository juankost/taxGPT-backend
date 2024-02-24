# Create a docker file for this project
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# Copy the repository and install the python package and dependencies
COPY . /workspace/src
WORKDIR /workspace/src

# Install Python pip and then install the package
RUN python3 -m pip install --no-cache-dir -e . 

# Option 3
RUN chmod +x /workspace/src/startup.sh
CMD ["/bin/bash", "/workspace/src/startup.sh"]