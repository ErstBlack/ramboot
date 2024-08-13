import os.path
import subprocess

MOVE_MOUNT_CMD = ["mount", "--move"]
COMMON_MOUNTS = ["dev", "proc", "sys", "run"]


def move_mount(source, target) -> None:
    subprocess.run(MOVE_MOUNT_CMD + [source, target])


def move_system_mounts(ramdisk_base) -> None:
    for mount in COMMON_MOUNTS:
        move_mount(f"{os.path.sep}{mount}", os.path.join(ramdisk_base, mount))
