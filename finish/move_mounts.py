import os.path
import subprocess

MOVE_MOUNT_CMD = ["mount", "--move"]
COMMON_MOUNTS = ["dev", "proc", "sys", "run"]


def move_mount(source: str, target: str) -> None:
    """
    Move a mount point from the source path to the target path.

    This function uses the `mount --move` command to relocate an existing mount
    point from the specified source to the target.

    Args:
        source (str): The source path of the mount point to be moved.
        target (str): The target path where the mount point should be moved.

    Returns:
        None
    """
    subprocess.run(MOVE_MOUNT_CMD + [source, target])


def move_system_mounts(ramdisk_base: str) -> None:
    """
    Move common system mounts (e.g., /dev, /proc, /sys, /run) to a new base directory.

    This function relocates the common system mounts to a new directory on a RAM disk,
    to ensure that they are properly mounted in the new environment.

    Args:
        ramdisk_base (str): The base directory on the RAM disk where the system mounts
                            should be moved.

    Returns:
        None
    """
    for mount in COMMON_MOUNTS:
        move_mount(f"{os.path.sep}{mount}", os.path.join(ramdisk_base, mount))
