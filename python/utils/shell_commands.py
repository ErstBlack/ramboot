import subprocess
import os
from typing import List


def check_output_wrapper(cmd: List[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def run_commands(*args: List[str]) -> None:
    for arg in args:
        # Early exit, if we don't have one of the commands, things will break anyway
        if not check_command(arg):
            return

        try:
            subprocess.run(arg)
        except FileNotFoundError:
            pass


def check_command(cmd: List[str]) -> bool:
    return os.path.exists(cmd[0])
