from common.fstab import get_all_mounts
from common.move_mounts import move_all_mounts
from common.pivot_root import pivot_root
from ramdisk.main_ramdisk import simple_ramdisk
from regular_part.copy.copy_mounts import copy_all_mounts
from regular_part.fstab.fix_fstab import replace_fstab
from regular_part.mounts.all_mounts import AllMounts

simple_ramdisk_boot = True


def part_boot() -> None:
    # Get all mounts mentioned in /etc/fstab
    all_mounts = AllMounts(get_all_mounts())

    # Get Physical Mounts
    physical_mounts = all_mounts.get_physical_mounts()
    physical_mounts.sort_by_depth()

    if simple_ramdisk_boot:
        # Get root disk size
        root_disk_size = physical_mounts.get_root_mount().get_parent_size_gb()

        # Create the ramdisk
        ramdisk_base = simple_ramdisk(root_disk_size)

    else:
        # TODO: Handle more complicated partitioning
        ramdisk_base = None

    # Copy mounts to the ramdisk
    copy_all_mounts(physical_mounts, ramdisk_base)

    # Move dev, proc, sys, and run to ramdisk
    move_all_mounts(ramdisk_base)

    # Fix fstab to prevent remounts
    replace_fstab(all_mounts, ramdisk_base)

    # Pivot Root
    pivot_root(ramdisk_base)
