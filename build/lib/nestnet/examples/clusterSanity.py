#!/usr/bin/env python

'''
A sanity check for cluster edition
'''

from nestnet.examples.cluster import MininetCluster
from nestnet.log import setLogLevel
from nestnet.examples.clustercli import ClusterCLI as CLI
from nestnet.topo import SingleSwitchTopo

def clusterSanity():
    "Sanity check for cluster mode"
    topo = SingleSwitchTopo()
    net = MininetCluster( topo=topo )
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    clusterSanity()
