from typing import List

from mounts.mount_info import MountInfo
from mounts.zfs_info import ZfsInfo, AllZfs
from utils.shell_commands import check_output_wrapper


def get_zfs_volumes() -> List[ZfsInfo]:
    zfs_list_cmd = ["/usr/sbin/zfs", "list", "-H", "-o", "name,mountpoint"]
    try:
        zfs_volumes = check_output_wrapper(zfs_list_cmd).split("\n")
    except FileNotFoundError:
        return []

    zfs_infos = []
    for idx, zfs_vol in enumerate(zfs_volumes):
        zfs_infos.append(ZfsInfo(zfs_vol, idx))

    return zfs_infos


def get_mounts() -> List[MountInfo]:
    zfs_volumes = AllZfs(get_zfs_volumes())

    return [zfs_vol.to_mount_info() for zfs_vol in zfs_volumes.zfs_list]
