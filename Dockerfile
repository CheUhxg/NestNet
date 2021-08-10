FROM ubuntu:bionic
LABEL maintainer="manuel@peuster.de"

# install required packages
RUN apt-get clean
RUN apt-get update \
    && apt-get install -y  git \
    net-tools \
    aptitude \
    build-essential \
    python3-setuptools \
    python3-dev \
    python3-pip \
    software-properties-common \
    ansible \
    curl \
    iptables \
    iputils-ping \
    sudo

# install nestnet (using its Ansible playbook)
COPY . /nestnet
WORKDIR /nestnet/ansible
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml
WORKDIR /nestnet
RUN make develop

# Hotfix: https://github.com/pytest-dev/pytest/issues/4770
RUN pip3 install "more-itertools<=5.0.0"

# tell nestnet that it runs in a container
ENV NESTNET_NESTED 1

# Important: This entrypoint is required to start the OVS service
ENTRYPOINT ["util/isula/entrypoint.sh"]
CMD ["python3", "examples/nestnet_example.py"]

