import os
from typing import List
from setup.mounts.mount_info import MountInfo, AllMounts
from utils.ramboot_config import RambootConfig


def read_fstab(fstab_file: str) -> List[str]:
    """
    Read the contents of the specified fstab file.

    Args:
        fstab_file (str): The path to the fstab file.

    Returns:
        List[str]: A list of strings, each representing a line in the fstab file.
    """
    with open(fstab_file, "r") as f:
        return f.readlines()


def cleanup_fstab(fstab_lines: List[str]) -> List[str]:
    """
    Clean up the lines of an fstab file by removing empty lines and comments.

    Args:
        fstab_lines (List[str]): A list of strings, each representing a line from the fstab file.

    Returns:
        List[str]: A list of cleaned lines with comments and empty lines removed.
    """
    clean_lines = (line for line in fstab_lines if line.strip())
    clean_lines = (line for line in clean_lines if not line.startswith("#") and len(line.strip()))

    return list(clean_lines)


def get_mounts() -> List[MountInfo]:
    """
    Retrieve and parse the mount information from the fstab file.

    Returns:
        List[MountInfo]: A list of MountInfo objects representing the mounts defined in the fstab file.
    """
    fstab = cleanup_fstab(read_fstab(RambootConfig.get_fstab_file()))
    return [MountInfo.create_mount_info(line) for line in fstab]


def replace_fstab(all_mounts: AllMounts, ramdisk_base: str) -> None:
    """
    Replace the fstab file with entries for non-physical mounts.

    Args:
        all_mounts (AllMounts): An object containing all mount information.
        ramdisk_base (str): The base directory for the RAM disk where the fstab file should be written.

    Returns:
        None
    """
    fstab_path = os.path.join(ramdisk_base, RambootConfig.get_fstab_file().lstrip(os.path.sep))
    fstab_lines = [mount.to_fstab_line() for mount in all_mounts if not mount.is_physical()]

    with open(fstab_path, "w") as f:
        f.writelines(line + os.linesep for line in fstab_lines)
