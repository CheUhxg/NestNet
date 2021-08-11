#!/usr/bin/env python

"clusterdemo.py: demo of Mininet Cluster Edition prototype"

from nestnet.examples.cluster import ( MininetCluster, SwitchBinPlacer,
                                       RemoteLink )
# ^ Could also use: RemoteSSHLink, RemoteGRELink
from nestnet.topolib import TreeTopo
from nestnet.log import setLogLevel
from nestnet.examples.clustercli import ClusterCLI as CLI

def demo():
    "Simple Demo of Cluster Mode"
    servers = [ 'localhost', 'ubuntu2', 'ubuntu3' ]
    topo = TreeTopo( depth=3, fanout=3 )
    net = MininetCluster( topo=topo, servers=servers, link=RemoteLink,
                          placement=SwitchBinPlacer )
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    demo()
