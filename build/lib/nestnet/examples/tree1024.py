#!/usr/bin/env python

"""
Create a 1024-host network, and run the CLI on it.
If this fails because of kernel limits, you may have
to adjust them, e.g. by adding entries to /etc/sysctl.conf
and running sysctl -p. Check util/sysctl_addon.
"""

from nestnet.cli import CLI
from nestnet.log import setLogLevel
from nestnet.node import OVSSwitch
from nestnet.topolib import TreeNet
from nestnet.examples.treeping64 import HostV4

if __name__ == '__main__':
    setLogLevel( 'info' )
    network = TreeNet( depth=2, fanout=32, host=HostV4,
                       switch=OVSSwitch, waitConnected=True)
    network.run( CLI, network )
