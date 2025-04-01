from subprocesclass PowershellExecuter:
    """

    """
    def execute(self, command, hidden):
        cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoLogo']  # '-File', 'C:\\Users\\name\\Documents\\test\\test.ps1']
        if hidden:
            cmd.append("-WindowStyle")
            cmd.append("hidden")
        for argument in command.split(" "):
            cmd.append(argument)


        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output = ""
        while True:
            line = proc.stdout.readline()
            if line != b'':
                output += line.strip()
            else:
                break
        return outputs import Popen, PIPE

