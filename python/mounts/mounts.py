from typing import List

from mounts.fstab import get_mounts
from mounts.mount_info import MountInfo, AllMounts
from utils.rambootconfig import RambootConfig


def check_for_ignored_mounts(mounts: List[MountInfo]) -> List[MountInfo]:
    ignored_mounts = RambootConfig.get_ignored_mounts()
    return [mount for mount in mounts if mount.dest not in ignored_mounts]


def get_all_mounts() -> AllMounts:
    fstab_mounts = get_mounts()

    # TODO: Include ZFS

    return AllMounts(fstab_mounts)
