
    def startShell(self, *args, **kwargs):
        "Start a shell process for running commands"
        if self.shell:
            error("%s: shell is already running\n" % self.name)
            return
        # mnexec: (c)lose descriptors, (d)etach from tty,
        # (p)rint pid, and run in (n)amespace
        # opts = '-cd' if mnopts is None else mnopts
        # if self.inNamespace:
        #     opts += 'n'
        # bash -i: force interactive
        # -s: pass $* to shell, and make process easy to find in ps
        # prompt is set to sentinel chr( 127 )
        cmd = ['isula', 'exec', '-it', '%s' % (self.did), 'env', 'PS1=' + chr(127),
               'bash', '--norc', '-is', 'mininet:' + self.name]
        # Spawn a shell subprocess in a pseudo-tty, to disable buffering
        # in the subprocess and insulate it from signals (e.g. SIGINT)
        # received by the parent
        
        self.master, self.slave = pty.openpty()
        self.shell = self._popen(cmd, stdin=self.slave, stdout=self.slave, stderr=self.slave,
                                 close_fds=False)
        self.stdin = os.fdopen(self.master, 'r')
        self.stdout = self.stdin
        self.pid = self._get_pid()
        self.pollOut = select.poll()
        self.pollOut.register(self.stdout)
        # Maintain mapping between file descriptors and nodes
        # This is useful for monitoring multiple nodes
        # using select.poll()
        self.outToNode[self.stdout.fileno()] = self
        self.inToNode[self.stdin.fileno()] = self
        self.execed = False
        self.lastCmd = None
        self.lastPid = None
        self.readbuf = ''
        print('host pid %s'%(self.pid))
        # Wait for prompt
        while True:
            data = self.read(1024)
            if data[-1] == chr(127):
                break          
            self.pollOut.poll()  
        
        self.waiting = False
        # +m: disable job control notification
        self.cmd('unset HISTFILE; stty -echo; set +m')