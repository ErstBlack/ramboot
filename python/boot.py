import json

from lvm.lvm_info import activate_vgs
from utils.disks import hide_disks
from utils.fstab import get_all_mounts
from utils.move_mounts import move_system_mounts
from utils.pivot_root import pivot_root
from ramdisk.main_ramdisk import simple_ramdisk, create_ramdisk, create_ramdisk_partitions
from utils.copy_mounts import copy_all_mounts
from utils.fstab import replace_fstab
from mounts.mount_info import AllMounts

# TODO: Create some sort of config file in /etc/conf holding this value
simple_ramdisk_boot = False
hide_disks_before_boot = True


def boot() -> None:
    # Attempt to activate vgs
    activate_vgs()

    # Get all mounts mentioned in /etc/fstab
    all_mounts = AllMounts(get_all_mounts())

    with open("/root/mount_info.json", "w") as f:
        for mount in all_mounts:
            f.write(json.dumps(mount.__dict__, indent=4))

    # Filter down to physical mounts
    physical_mounts = all_mounts.get_physical_mounts()

    # Check if we want a single (one partition) ramdisk
    if simple_ramdisk_boot:
        # Get root partition
        root_mount = physical_mounts.get_root_mount()

        # Create the ramdisk based on the root partition
        ramdisk_base = simple_ramdisk(root_mount)

    else:
        # Create a partition representation for all the physical mounts
        all_ramdisk_partitions = create_ramdisk_partitions(physical_mounts)

        # Create a ramdisk based on the partitioning setup
        ramdisk_base = create_ramdisk(all_ramdisk_partitions)

    # Copy mounts to the ramdisk
    copy_all_mounts(physical_mounts, ramdisk_base)

    # Fix fstab to prevent remounts
    replace_fstab(all_mounts, ramdisk_base)

    # Move dev, proc, sys, and run to ramdisk
    move_system_mounts(ramdisk_base)

    # Pivot Root
    pivot_root(ramdisk_base)

    # Hide block devices used for mounts
    if hide_disks_before_boot:
        hide_disks(all_mounts)
