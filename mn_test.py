#!/usr/bin/env python

"""
查看命令行参数: sudo mn -h

使用定制网络: sudo mn --custom ~/mininet/custom/custom_example.py
"""

import os
import sys
import time

from functools import partial
import argparse
from sys import exit
from typing import Container

# 修复漏洞
if 'PYTHONPATH' in os.environ:
    sys.path = os.environ[ 'PYTHONPATH' ].split( ':' ) + sys.path

from nestnet.clean import cleanup
import nestnet.cli
from nestnet.log import lg, LEVELS, info, debug, warn, error, output
from nestnet.net import Containernet, Mininet, MininetWithControlNet, VERSION
from nestnet.node import ( Host, Isula, CPULimitedHost, Controller, OVSController,
                           Ryu, NOX, RemoteController, findController,
                           DefaultController, NullController,
                           UserSwitch, OVSSwitch, OVSBridge,
                           IVSSwitch )
from nestnet.nodelib import LinuxBridge
from nestnet.link import Link, TCLink, TCULink, OVSLink
from nestnet.topo import ( SingleSwitchTopo, LinearTopo,
                           SingleSwitchReversedTopo, MinimalTopo )
from nestnet.topolib import TreeTopo, TorusTopo
from nestnet.util import customClass, specialClass, splitArgs, buildTopo

# 用于实验的集群原型
from nestnet.examples.cluster import ( MininetCluster, RemoteHost,
                                       RemoteOVSSwitch, RemoteLink,
                                       SwitchBinPlacer, RandomPlacer,
                                       ClusterCleanup )
from nestnet.examples.clustercli import ClusterCLI


PLACEMENT = { 'block': SwitchBinPlacer, 'random': RandomPlacer }

# 建立拓扑的参数集
TOPODEF = 'minimal'
TOPOS = { 'minimal': MinimalTopo,
          'linear': LinearTopo,
          'reversed': SingleSwitchReversedTopo,
          'single': SingleSwitchTopo,
          'tree': TreeTopo,
          'torus': TorusTopo }

SWITCHDEF = 'default'
SWITCHES = { 'user': UserSwitch,
             'ovs': OVSSwitch,
             'ovsbr' : OVSBridge,
             'ovsk': OVSSwitch,
             'ivs': IVSSwitch,
             'lxbr': LinuxBridge,
             'default': OVSSwitch }

HOSTDEF = 'proc'
HOSTS = { 'proc': Host,
          'isula': Isula,
          'rt': specialClass( CPULimitedHost, defaults=dict( sched='rt' ) ),
          'cfs': specialClass( CPULimitedHost, defaults=dict( sched='cfs' ) ) }

CONTROLLERDEF = 'default'
CONTROLLERS = { 'ref': Controller,
                'ovsc': OVSController,
                'nox': NOX,
                'remote': RemoteController,
                'ryu': Ryu,
                'default': DefaultController,  # Note: overridden below
                'none': NullController }

LINKDEF = 'default'
LINKS = { 'default': Link,
          'tc': TCLink,
          'tcu': TCULink,
          'ovs': OVSLink }

# TEST字典集可以包含函数和/或mininet()方法名称
TESTS = { name: True
          for name in ( 'pingall', 'pingpair', 'iperf', 'iperfudp' ) }

CLI = None

# 本地定义测试
def allTest( net ):
    "Run ping and iperf tests"
    net.waitConnected()
    net.start()
    net.ping()
    net.iperf()

def nullTest( _net ):
    "Null 'test' (does nothing)"
    pass


TESTS.update( all=allTest, none=nullTest, build=nullTest )

# 映射到Mininet()方法的备用拼写
ALTSPELLING = { 'pingall': 'pingAll', 'pingpair': 'pingPair',
                'iperfudp': 'iperfUdp' }

def runTests( mn, args ):
    """运行测试
       mn: Mininet对象
       arg: 测试选项列表 """
    # 将选项分成测试名称和参数
    for arg in args:
        # 现在可以通过'+'分开多个测试
        for test in arg.split( '+' ):
            test, args, kwargs = splitArgs( test )
            test = ALTSPELLING.get( test.lower(), test )
            testfn = TESTS.get( test, test )
            if callable( testfn ):
                testfn( mn, *args, **kwargs )
            elif hasattr( mn, test ):
                getattr( mn, test )( *args, **kwargs )
            else:
                raise Exception( 'Test %s is unknown - please specify one of '
                                 '%s ' % ( test, TESTS.keys() ) )


def addArguments( parser, choicesDict, default, name, **kwargs ):
    """方便函数将选择添加到ArgumentParser.
       args: ArgumentParser实例
       choicesDict: 有效选择的字典，必须包括默认值
       default: 默认选择键
       name: 参数名称
       kwargs: add_argument的其他参数"""
    helpStr = ( '|'.join( sorted( choicesDict.keys() ) ) +
                '[,param=value...]' )
    helpList = [ '%s=%s' % ( k, v.__name__ )
                 for k, v in choicesDict.items() ]
    helpStr += ' ' + ( ' '.join( helpList ) )
    params = dict( type=str, default=default, help=helpStr )
    params.update( **kwargs )
    parser.add_argument( '--' + name, **params )

def version( *_args ):
    "打印mininet版本和退出."
    output( "%s\n" % VERSION )
    exit()


class MininetRunner( object ):
    "构建，设置和运行nestnet."

    def __init__( self ):
        "Init."
        self.args = None
        self.validate = None

        self.parseArgs()
        self.setup()
        self.begin()

    def custom( self, value ):
        """解析自定义文件和添加参数.
           value: 遵循该参数的列表"""
        files = value

        for fileName in files:
            customs = {}
            if os.path.isfile( fileName ):
                # pylint: disable=exec-used
                exec( compile( open( fileName ).read(), fileName, 'exec' ),
                      customs, customs )
                for name, val in customs.items():
                    self.setCustom( name, val )
            else:
                raise Exception( 'could not find custom file: %s' % fileName )

    def setCustom( self, name, value ):
        "为mininetrunner设置自定义参数."
        if name in ( 'topos', 'switches', 'hosts', 'controllers', 'links'
                     'testnames', 'tests' ):
            # 更新词典
            param = name.upper()
            globals()[ param ].update( value )
        elif name == 'validate':
            # 添加自定义验证功能
            self.validate = value
        else:
            # 添加或修改全局变量或类
            globals()[ name ] = value

    def parseArgs( self ):
        "解析命令行参数并返回args对象."

        desc = ( "The %(prog)s utility creates Mininet network from the\n"
                 "command line. It can create parametrized topologies,\n"
                 "invoke the Mininet CLI, and run tests." )

        usage = ( '%(prog)s [args]\n'
                  '(type %(prog)s -h for details)' )

        parser = argparse.ArgumentParser( description=desc, usage=usage )
        addArguments( parser, SWITCHES, SWITCHDEF, 'switch' )
        addArguments( parser, HOSTS, HOSTDEF, 'host' )
        addArguments( parser, CONTROLLERS, [], 'controller', action='append' )
        addArguments( parser, LINKS, LINKDEF, 'link' )
        addArguments( parser, TOPOS, TOPODEF, 'topo' )

        parser.add_argument( '--clean', '-c', action='store_true',
                         default=False, help='clean and exit' )
        parser.add_argument( '--custom', action='extend',
                         nargs='+',
                         type=str,
                         help='read custom classes or params from .py file(s)'
                         )
        parser.add_argument( '--test', default=[], action='append',
                         dest='test', help='|'.join( TESTS.keys() ) )
        parser.add_argument( '--xterms', '-x', action='store_true',
                         default=False, help='spawn xterms for each node' )
        parser.add_argument( '--ipbase', '-i', type=str, default='10.0.0.0/8',
                         help='base IP address for hosts' )
        parser.add_argument( '--mac', action='store_true',
                         default=False, help='automatically set host MACs' )
        parser.add_argument( '--arp', action='store_true',
                         default=False, help='set all-pairs ARP entries' )
        parser.add_argument( '--verbosity', '-v', type=str,
                         choices=list( LEVELS.keys() ), default = 'info',
                         help = '|'.join( LEVELS.keys() )  )
        parser.add_argument( '--innamespace', action='store_true',
                         default=False, help='sw and ctrl in namespace?' )
        parser.add_argument( '--listenport', type=int, default=6654,
                         help='base port for passive switch listening' )
        parser.add_argument( '--nolistenport', action='store_true',
                         default=False, help="don't use passive listening " +
                         "port")
        parser.add_argument( '--pre', type=str, default=None,
                         help='CLI script to run before tests' )
        parser.add_argument( '--post', type=str, default=None,
                         help='CLI script to run after tests' )
        parser.add_argument( '--pin', action='store_true',
                         default=False, help="pin hosts to CPU cores "
                         "(requires --host cfs or --host rt)" )
        parser.add_argument( '--nat',
                         help="[option=val...] adds a NAT to the topology that"
                         " connects Mininet hosts to the physical network."
                         " Warning: This may route any traffic on the machine"
                         " that uses Mininet's"
                         " IP subnet into the Mininet network."
                         " If you need to change"
                         " Mininet's IP subnet, see the --ipbase option." )
        parser.add_argument( '--version', action='version', 
                        #  callback=version,
                         version='%s\n' % VERSION,
                         help='prints the version and exits' )
        parser.add_argument( '--wait', '-w', action='store_true',
                         default=False, help='wait for switches to connect' )
        parser.add_argument( '--twait', '-t', action='store', type=int,
                         dest='wait',
                         help='timed wait (s) for switches to connect' )
        parser.add_argument( '--cluster', type=str, default=None,
                         metavar='server1,server2...',
                         help=( 'run on multiple servers (experimental!)' ) )
        parser.add_argument( '--placement', type=str,
                         choices=list( PLACEMENT.keys() ), default='block',
                         metavar='block|random',
                         help=( 'node placement for --cluster '
                                '(experimental!) ' ) )
        # parser.add_argument( '--isula', action='store_true',
        #                  default='../examples/containernet_example.py',
        #                  help='read container classes or params from .py file(s)')

        self.args = parser.parse_args()
        args = vars(self.args)
        # 运行函数处理参数
        if args['custom']:
            self.custom(args['custom'])

    def setup( self ):
        "设置和验证环境."

        # 设置日志记录效果
        if LEVELS[self.args.verbosity] > LEVELS['output']:
            warn( '*** WARNING: selected verbosity level (%s) will hide CLI '
                    'output!\n'
                    'Please restart Mininet with -v [debug, info, output].\n'
                    % self.args.verbosity )
        lg.setLogLevel( self.args.verbosity )

    def begin( self ):
        "创建和运行nestnet."

        global CLI

        args = self.args

        if args.cluster:
            servers = args.cluster.split( ',' )
            for server in servers:
                ClusterCleanup.add( server )

        if args.clean:
            cleanup()
            exit()

        start = time.time()

        if not args.controller:
            # 根据可用的控制器更新默认值
            CONTROLLERS[ 'default' ] = findController()
            args.controller = [ 'default' ]
            if not CONTROLLERS[ 'default' ]:
                args.controller = [ 'none' ]
                if args.switch == 'default':
                    info( '*** No default OpenFlow controller found '
                          'for default switch!\n' )
                    info( '*** Falling back to OVS Bridge\n' )
                    args.switch = 'ovsbr'
                elif args.switch not in ( 'ovsbr', 'lxbr' ):
                    raise Exception( "Could not find a default controller "
                                     "for switch %s" %
                                     args.switch )

        topo = buildTopo( TOPOS, args.topo )
        switch = customClass( SWITCHES, args.switch )
        host = customClass( HOSTS, args.host )
        controller = [ customClass( CONTROLLERS, c )
                       for c in args.controller ]
        
        if args.switch == 'user' and args.link == 'default':
            debug( '*** Using TCULink with UserSwitch\n' )
            # 使用正确配置的链接
            args.link = 'tcu'

        link = customClass( LINKS, args.link )
        
        if args.host == 'isula':
            Net = Containernet
            mn = Net( topo=topo, config={'image':'ubuntu:trusty',
                    'cmd':['/bin/bash',]
                    },
                    switch=switch, host=host, controller=controller, link=link,
                    ipBase=args.ipbase, inNamespace=args.innamespace,
                    xterms=args.xterms, autoSetMacs=args.mac,
                    autoStaticArp=args.arp, autoPinCpus=args.pin,
                    waitConnected=args.wait,
                    listenPort=args.listenport )
        else:
            if self.validate:
                self.validate( args )

            if args.nolistenport:
                args.listenport = None

            if args.innamespace and args.cluster:
                error( "Please specify --innamespace OR --cluster\n" )
                exit()
            Net = MininetWithControlNet if args.innamespace else Mininet
            if args.cluster:
                warn( '*** WARNING: Experimental cluster mode!\n'
                    '*** Using RemoteHost, RemoteOVSSwitch, RemoteLink\n' )
                host, switch, link = RemoteHost, RemoteOVSSwitch, RemoteLink
                Net = partial( MininetCluster, servers=servers,
                            placement=PLACEMENT[ args.placement ] )
                nestnet.cli.CLI = ClusterCLI
            
            mn = Net( topo=topo,
                    switch=switch, host=host, controller=controller, link=link,
                    ipBase=args.ipbase, inNamespace=args.innamespace,
                    xterms=args.xterms, autoSetMacs=args.mac,
                    autoStaticArp=args.arp, autoPinCpus=args.pin,
                    waitConnected=args.wait,
                    listenPort=args.listenport )

        CLI = nestnet.cli.CLI if CLI is None else CLI

        if args.pre:
            CLI( mn, script=args.pre )

        mn.start()

        if args.test:
            runTests( mn, args.test )
        else:
            CLI( mn )

        if args.post:
            CLI( mn, script=args.post )

        mn.stop()

        elapsed = float( time.time() - start )
        info( 'completed in %0.3f seconds\n' % elapsed )


if __name__ == "__main__":
    try:
        MininetRunner()
    except KeyboardInterrupt:
        info( "\n\nKeyboard Interrupt. Shutting down and cleaning up...\n\n")
        cleanup()
    except Exception:  # pylint: disable=broad-except
        # Print exception
        type_, val_, trace_ = sys.exc_info()
        errorMsg = ( "-"*80 + "\n" +
                     "Caught exception. Cleaning up...\n\n" +
                     "%s: %s\n" % ( type_.__name__, val_ ) +
                     "-"*80 + "\n" )
        error( errorMsg )
        # 打印堆栈跟踪以调试日志
        import traceback
        stackTrace = traceback.format_exc()
        print(stackTrace)
        debug( stackTrace + "\n" )
        cleanup()
