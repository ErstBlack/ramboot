import os.path
import subprocess
from glob import glob
from typing import List

from utils.ramboot_config import RambootConfig


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


def activate_vgs() -> None:
    activate_cmd = ["/usr/sbin/vgchange", "-a", "y"]
    mknode_cmd = ["/usr/sbin/vgscan", "--mknodes"]

    run_commands(activate_cmd, mknode_cmd)


def scan_btrfs() -> None:
    scan_cmd = ["/usr/sbin/btrfs", "device", "scan", "--all"]

    run_commands(scan_cmd)


def import_zpools() -> None:
    import_cmd = ["/usr/bin/zpool", "import", "-a"]

    run_commands(import_cmd)


def assemble_md() -> None:
    assemble_cmd = ["/usr/sbin/mdadm", "--assemble", "--scan"]
    udevadm_cmd = ["/usr/sbin/udevadm", "test"]

    run_commands(assemble_cmd)

    # Adding the question mark so we don't match the directory /dev/md
    md_files = glob("/dev/md?*")
    for file in md_files:
        run_commands(udevadm_cmd + [file])


def initial_activations() -> None:
    if RambootConfig.get_activate_field("raid"):
        assemble_md()
    if RambootConfig.get_activate_field("zfs"):
        import_zpools()
    if RambootConfig.get_activate_field("btrfs"):
        scan_btrfs()
    if RambootConfig.get_activate_field("lvm"):
        activate_vgs()
