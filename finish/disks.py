import itertools
import os.path

from glob import glob
from setup.mounts.mount_info import AllMounts
from utils.ramboot_config import RambootConfig


def delete_zpool_cache() -> None:
    cache_file = "/etc/zfs/zpool.cache"
    zfs_list_dir = "/etc/zfs/zfs-list.cache"

    list_cache_files = glob(os.path.join(zfs_list_dir, "*"))

    for f in list_cache_files + [cache_file]:
        if os.path.exists(f) and os.path.isfile(f):
            os.remove(f)


def mask_zfs_targets() -> None:
    target_dir = "/etc/systemd/system"

    # Most commonly used zfs targets, might want to allow user to add additional/overwrite via config
    target_files = ["zfs-volumes.target", "zfs-import.target", "zfs.target"]

    for target_file in target_files:
        os.symlink("/dev/null", os.path.join(target_dir, target_file))


def hide_zpools(all_mounts: AllMounts) -> None:
    """
    Hide ZFS zpools by removing ZFS cache files.

    This function deletes the ZFS cache files to prevent ZFS zpools from being recognized
    by the system after reboot.

    Args:
        all_mounts (AllMounts): An object containing all the mount information.

    Returns:
        None
    """
    if all_mounts.get_root_mount().fstype != "zfs":
        return

    delete_zpool_cache()
    mask_zfs_targets()


def hide_disks(all_mounts: AllMounts) -> None:
    """
    Hide disks by removing ZFS zpools and block devices based on the system configuration.

    This function first hides ZFS zpools if the root filesystem is ZFS,
    then hides block devices if configured to do so.

    Args:
        all_mounts (AllMounts): An object containing all the mount information.

    Returns:
        None
    """
    hide_zpools(all_mounts)
    hide_block_devices(all_mounts)


def hide_block_devices(all_mounts: AllMounts) -> None:
    """
    Hide block devices by triggering their deletion in the system if configured to hide disks.

    This function removes devices / volumes from the system by writing to the appropriate
    sysfs files. This operation is performed only if the root filesystem is on an LVM
    and the configuration allows for disk hiding.

    Args:
        all_mounts (AllMounts): An object containing all the mount information, including the root mount.

    Returns:
        None
    """
    if not RambootConfig.get_hide_disks():
        return

    # TODO: See if there's a way to handle this nicely for regular root partition.
    # TODO: Test for zfs and btrfs
    # TODO: Add luks check, luks breaks this
    # Maybe create a baby ramdisk only to hold the ramboot.sh?
    # Could probably get this working with a systemd or equivalent service that runs after the init?
    if not all_mounts.get_root_mount().is_lvm():
        return

    path_prefix = "/sys/block"
    path_suffix = "device/delete"

    # Get all parent_disks
    disks = [mount.get_parent_disks() for mount in all_mounts if mount.get_parent_disks() is not None]

    # Unpack nested lists, get the basename, then remove duplicates
    # i.e.
    # [[ /dev/sda, /dev/sdb ], [ /dev/sda, /dev/sdb ]] -> { sda, sdb }
    disks = set(os.path.basename(disk) for disk in itertools.chain.from_iterable(disks))

    for disk in disks:
        delete_path = os.path.join(path_prefix, disk, path_suffix)

        if os.path.exists(delete_path):
            with open(delete_path, "w") as f:
                f.write('1')
