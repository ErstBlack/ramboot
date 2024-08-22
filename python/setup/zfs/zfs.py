from typing import List

from setup.mounts.mount_info import MountInfo
from setup.zfs.zfs_info import ZfsInfo, AllZfs
from utils.shell_commands import check_output_wrapper

from typing import List


def get_zfs_volumes() -> List[ZfsInfo]:
    """
    Retrieve the list of ZFS volumes on the system.

    This function executes the `zfs list` command to get a list of ZFS volumes
    along with their mount points. It parses the output and returns a list of
    ZfsInfo objects representing each volume.

    Returns:
        List[ZfsInfo]: A list of ZfsInfo objects representing the ZFS volumes.
        If the `zfs` command is not found, an empty list is returned.
    """
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
    """
    Retrieve the list of mounts for the ZFS volumes.

    This function retrieves the list of ZFS volumes and converts them into
    MountInfo objects, representing the mounts for each ZFS volume.

    Returns:
        List[MountInfo]: A list of MountInfo objects representing the mounts
        associated with the ZFS volumes.
    """
    zfs_volumes = AllZfs(get_zfs_volumes())

    return [zfs_vol.to_mount_info() for zfs_vol in zfs_volumes.zfs_list]
