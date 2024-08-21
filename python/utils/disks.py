import os.path

from glob import glob
from mounts.mount_info import AllMounts
from utils.ramboot_config import RambootConfig


def hide_zpools(all_mounts):
    if all_mounts.get_root_mount().fstype != "zfs":
        return

    cache_file = "/etc/zfs/zpool.cache"

    if os.path.exists(cache_file) and os.path.isfile(cache_file):
        os.remove(cache_file)

    list_dir = "/etc/zfs/zfs-list.cache"
    list_cache_files = glob(os.path.join(list_dir, "*"))

    for f in list_cache_files:
        if os.path.exists(f) and os.path.isfile(f):
            os.remove(f)


def hide_disks(all_mounts: AllMounts) -> None:
    hide_zpools(all_mounts)
    hide_block_devices(all_mounts)


def hide_block_devices(all_mounts: AllMounts):
    if RambootConfig.get_hide_disks():
        return

    # TODO: See if there's a way to handle this nicely for regular root partition.
    # Maybe create a baby ramdisk only to hold the ramboot.sh?
    if not all_mounts.get_root_mount().is_lvm():
        return

    path_prefix = "/sys/block"
    path_suffix = "device/delete"
    # Get all disks, e.g. sda, sdb, etc.
    disks = {os.path.basename(mount.get_parent_disk()) for mount in all_mounts if mount.get_parent_disk() is not None}

    for disk in disks:
        delete_path = os.path.join(path_prefix, disk, path_suffix)

        if os.path.exists(delete_path):
            with open(delete_path, "w") as f:
                f.write('1')
