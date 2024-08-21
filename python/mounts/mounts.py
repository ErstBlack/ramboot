from typing import List

from mounts import fstab, zfs
from mounts.mount_info import MountInfo, AllMounts
from utils.ramboot_config import RambootConfig


def check_for_ignored_mounts(mounts: List[MountInfo]) -> List[MountInfo]:
    ignored_mounts = RambootConfig.get_ignored_mounts()
    return [mount for mount in mounts if mount.dest not in ignored_mounts]


def get_all_mounts() -> AllMounts:
    fstab_mounts = fstab.get_mounts()
    zfs_mounts = zfs.get_mounts()

    all_mounts = check_for_ignored_mounts(fstab_mounts + zfs_mounts)

    # TODO: Include ZFS
    return AllMounts(all_mounts)
