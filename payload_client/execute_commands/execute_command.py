import platform

from payload_client.execute_commands.powershell import PowershellExecuter


class CodeExecutor():
    def __init__(self):
        self.os = platform.system()
        if self.os == "Windows":
            self.executor = PowershellExecuter()
        elif self.os == "Darwin":
            pass #MacOS
        else:
            pass #LINUX

    def execute(self, command, hidden=True):
        return self.executor.execute(command, hidden)