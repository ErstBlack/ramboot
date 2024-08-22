import subprocess

from utils.shell_commands import check_output_wrapper


def check_if_raid(device: str) -> bool:
    check_raid_cmd = ["lsblk", "--output", "TYPE", "--noheadings"]
    raid_prefix = "raid"

    try:
        output = check_output_wrapper(check_raid_cmd + [device]).lower()
    except subprocess.CalledProcessError:
        return False

    return output.startswith(raid_prefix)
