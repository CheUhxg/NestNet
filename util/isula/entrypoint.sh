#! /bin/bash -e

# start OVS
service openvswitch-switch start

# check if isula socket is mounted
if [ ! -S /var/run/isula.sock ]; then
    echo 'Error: the iSula socket file "/var/run/isula.sock" was not found. It should be mounted as a volume.'
    exit 1
fi

# this cannot be done from the Dockerfile since we have the socket not mounted during build
set +e
echo 'Pulling the "ubuntu:trusty" and "ubuntu:xenial" image for later use...'
isula pull 'ubuntu:trusty'
isula pull 'ubuntu:xenial'
set -e

echo "Welcome to Containernet running within a iSula container ..."

if [[ $# -eq 0 ]]; then
    exec /bin/bash
else
    exec $*
fi
