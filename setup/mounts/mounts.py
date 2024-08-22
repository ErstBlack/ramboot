from typing import List

from setup.mounts import fstab
from setup.zfs import zfs
from setup.mounts.mount_info import MountInfo, AllMounts
from utils.ramboot_config import RambootConfig


def check_for_ignored_mounts(mounts: List[MountInfo]) -> List[MountInfo]:
    """
    Remove mounts that are requested to be ignored.

    Args:
        mounts: A list of MountInfos representing all the known mounts on the system.

    Returns:
        List[MountInfo]: The remaining MountInfos after removing ignored Mounts
    """
    ignored_mounts = RambootConfig.get_ignored_mounts()
    return [mount for mount in mounts if mount.dest not in ignored_mounts]


def get_all_mounts() -> AllMounts:
    """
    Collect all known mounts on the system.

    Returns:
        AllMounts: The AllMounts object representing all the known mounts on the system.
    """
    fstab_mounts = fstab.get_mounts()
    zfs_mounts = zfs.get_mounts()

    all_mounts = check_for_ignored_mounts(fstab_mounts + zfs_mounts)

    # TODO: Include ZFS
    return AllMounts(all_mounts)
