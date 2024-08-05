from common.fstab import get_all_mounts
from common.move_mounts import move_all_mounts
from common.pivot_root import pivot_root
from ramdisk.main_ramdisk import simple_ramdisk
from regular_part.copy.copy_mounts import copy_all_mounts
from regular_part.fstab.fix_fstab import replace_fstab
from regular_part.mounts.all_mounts import AllMounts


def part_boot() -> None:
    # Get all mounts mentioned in /etc/fstab
    all_mounts = AllMounts(get_all_mounts())

    # Get Physical Mounts
    physical_mounts = all_mounts.get_physical_mounts()
    physical_mounts.sort_by_depth()

    # Get root disk size
    root_disk_size = physical_mounts.get_root_mount().get_parent_size_gb()

    # Create the ramdisk
    ramdisk_base = simple_ramdisk(root_disk_size + max(2, int(root_disk_size * 0.02)))

    # Copy mounts to the ramdisk
    copy_all_mounts(physical_mounts, ramdisk_base)

    # Move dev, proc, sys, and run to ramdisk
    move_all_mounts(ramdisk_base)

    # Fix fstab to prevent remounts
    replace_fstab(all_mounts, ramdisk_base)

    # Pivot Root and Init
    pivot_root(ramdisk_base)
