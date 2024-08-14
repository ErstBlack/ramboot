import os.path

from mounts.mount_info import AllMounts


def hide_disks(all_mounts: AllMounts) -> None:
    path_prefix = "/sys/block"
    path_suffix = "device/delete"
    # Get all disks, e.g. sda, sdb, etc.
    disks = {os.path.basename(mount.get_parent_disk()) for mount in all_mounts if mount.get_parent_disk()}

    for disk in disks:
        delete_path = os.path.join(path_prefix, disk, path_suffix)

        if os.path.exists(delete_path):
            with open(delete_path, "w") as f:
                f.write('1')
