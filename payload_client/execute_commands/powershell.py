import subprocess
from subprocess import Popen, PIPE


class PowershellExecuter:
    def execute(self, command, hidden):
        cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoLogo']  # '-File', 'C:\\Users\\name\\Documents\\test\\test.ps1']
        if hidden:
            cmd.append("-WindowStyle")
            cmd.append("hidden")
        for argument in command.split(" "):
            cmd.append(argument)


        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = ""
        while True:
            line = proc.stdout.readline()
            if line != b'':

                output += line.strip().decode("utf-8")
                output += "\n"
            else:
                break
        return output