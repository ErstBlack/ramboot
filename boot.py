from startup.initial_activations import initial_activations
from finish.disks import hide_disks
from setup.mounts.mounts import get_all_mounts
from finish.move_mounts import move_system_mounts
from finish.pivot_root import pivot_root
from setup.ramdisk.main_ramdisk import create_ramdisk
from setup.ramdisk.copy_mounts import copy_all_mounts
from setup.mounts.fstab import replace_fstab


def boot() -> None:
    """
    Kickoff function to start the ramboot

    Returns:
        None
    """

    # Attempt to activate/scan filesystems
    initial_activations()

    # Get all mounts mentioned in /etc/fstab
    all_mounts = get_all_mounts()

    # Filter down to physical mounts
    physical_mounts = all_mounts.get_physical_mounts()

    # Create the ramdisk
    ramdisk_base = create_ramdisk(physical_mounts)

    # Copy mounts to the ramdisk
    copy_all_mounts(physical_mounts, ramdisk_base)

    # Fix fstab to prevent remounts
    replace_fstab(all_mounts, ramdisk_base)

    # Move dev, proc, sys, and run to ramdisk
    move_system_mounts(ramdisk_base)

    # Pivot Root
    pivot_root(ramdisk_base)

    # Hide devices used for mounts
    hide_disks(all_mounts)
