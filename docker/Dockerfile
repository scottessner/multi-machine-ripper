# Start with latest LTS of Ubuntu
FROM ubuntu:latest

# Install basic dependencies
RUN apt update && apt install -y --no-install-recommends \
    python3 \
    python3-pip \
    git

# Set up links to refer to python3 versions of python and pip
RUN cd /usr/bin \
    && ln -s python3 python \
    && ln -s pip3 pip

# Set up directory and download software from git
RUN cd /opt \
    && git clone https://github.com/scottessner/multi-machine-ripper.git

# Install python requirements
RUN cd /opt/multi-machine-ripper \
    && pip install -r requirements.txt

EXPOSE 1900
EXPOSE 22




