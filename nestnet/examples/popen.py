#!/usr/bin/env python

"""
This example monitors a number of hosts using host.popen() and
pmonitor()
"""

from nestnet.net import Mininet
from nestnet.topo import SingleSwitchTopo
from nestnet.log import setLogLevel, info
from nestnet.util import pmonitor

def monitorhosts( hosts=5 ):
    "Start a bunch of pings and monitor them using popen"
    mytopo = SingleSwitchTopo( hosts )
    net = Mininet( topo=mytopo, waitConnected=True )
    net.start()
    # Start a bunch of pings
    popens = {}
    last = net.hosts[ -1 ]
    for host in net.hosts:
        popens[ host ] = host.popen( "ping -c5 %s" % last.IP() )
        last = host
    # Monitor them and print output
    for host, line in pmonitor( popens ):
        if host:
            info( "<%s>: %s" % ( host.name, line ) )
    # Done
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    monitorhosts( hosts=5 )
