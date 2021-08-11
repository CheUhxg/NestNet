#!/usr/bin/env python

"""
Example to create a Mininet topology and connect it to the internet via NAT
"""


from nestnet.cli import CLI
from nestnet.log import lg, info
from nestnet.topolib import TreeNet


if __name__ == '__main__':
    lg.setLogLevel( 'info')
    net = TreeNet( depth=1, fanout=4, waitConnected=True )
    # Add NAT connectivity
    net.addNAT().configDefault()
    net.start()
    info( "*** Hosts are running and should have internet connectivity\n" )
    info( "*** Type 'exit' or control-D to shut down network\n" )
    CLI( net )
    # Shut down NAT
    net.stop()
