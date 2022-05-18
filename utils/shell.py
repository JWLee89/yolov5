import subprocess
import typing as t


class ShellUtil:
    """
    Class that is responsible for executing tasks safely via the command line.
    Please also be warned that this might be extremely risky when using commands like 'rm'.
    Please use this API responsibly.
    """

    @staticmethod
    def _get_commands_from_str(command_to_execute: str) -> t.List[t.List[str]]:
        """
        Args:
            command_to_execute: The command to execute in string. E.g. "ls -l; pwd;"
        Returns:
            The command to execute converted into a list.
            E.g. [ ['ls', '-l'], ['pwd'] ]
        """
        commands: t.List = command_to_execute.strip().split(';')
        return ShellUtil._get_commands(commands)

    @staticmethod
    def _get_commands(commands: t.Union[t.List, t.Tuple]) -> t.List[t.List[str]]:
        """
        Args:
            commands: A list of commands to execute
        Returns:
            A list of commands, converted into a list delimited by a space.
            This is to match the format of data accepted by subprocess.
        """
        return [command.split() for command in commands if len(command) > 0]

    @staticmethod
    def parse_shell_command(command_to_execute: t.Union[t.List[str], t.Tuple[str], str]) -> t.List[t.List[str]]:
        """
        Given a command, parse the commands into a list of multiple sub-commands.
        E.g. python3 test.py; cd teemo;
        will become [ ['python3', 'test.py'], ['cd', 'teemo'] ]
        """
        if isinstance(command_to_execute, str):
            return ShellUtil._get_commands_from_str(command_to_execute)
        elif isinstance(command_to_execute, (t.List, t.Tuple)):
            commands_to_run = []
            for command in command_to_execute:
                commands_to_run += ShellUtil._get_commands_from_str(command)
            return commands_to_run
        else:
            raise TypeError('command_to_execute must be a string, list or tuple of commands')

    @staticmethod
    def subprocess_run(commands: t.Union[t.List[str], t.Tuple[str], str], **kwargs):
        """
        Execute set of commands.
        Args:
            commands: (t.List[t.List[str]]) A list, tuple or string of commands.
            E.g. 'python3 test.py; cd teemo;',  [ ['python3', 'test.py'], ['cd', 'teemo'] ],
                 ( ['python3', 'test.py'], ['cd', 'teemo'] )
            cwd: The working directory to run the command in

        Returns:
            ShellExecutor: The class instance so that we can chain the commands
        """
        commands_to_execute = ShellUtil.parse_shell_command(commands)
        for command in commands_to_execute:
            subprocess.run(command, **kwargs)
        return ShellUtil
