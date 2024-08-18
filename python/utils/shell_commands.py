import subprocess
from typing import List


def check_output_wrapper(cmd: List[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()
