import os
import subprocess

from setup.ramdisk.ramdisk_part_info import AllRamdiskPartInfo, RamdiskPartInfo
from setup.mounts.mount_info import AllMounts, MountInfo
from utils.ramboot_config import RambootConfig

RAMDISK_DEV = "/dev/ram0"
RAMDISK_BASE = "/mnt/ramdisk-ramboot"


def modprobe_ramdisk(size_in_gb: int, num_partitions: int) -> None:
    """
    Create a RAM disk by loading the `brd` module with the specified size and number of partitions.

    Args:
        size_in_gb (int): The total size of the RAM disk in gigabytes.
        num_partitions (int): The number of partitions to create on the RAM disk.

    Returns:
        None
    """
    # Create the Ramdisk, specifying the number of partitions and the total size
    modprobe_cmd = ["/usr/sbin/modprobe", "brd", "rd_nr=1", f"max_part={num_partitions}",
                    f"rd_size={1024 * 1024 * size_in_gb}"]

    subprocess.run(modprobe_cmd)


def partition_ramdisk(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
    """
    Partition the RAM disk according to the specified partition information.

    Args:
        all_ramdisk_partitions (AllRamdiskPartInfo): An object containing partition information for the RAM disk.

    Returns:
        None
    """
    sgdisk_cmd = ["/usr/sbin/sgdisk", "--zap-all"]

    for part_info in all_ramdisk_partitions:
        # Build command one partition at a time
        sgdisk_cmd.append("--new")
        sgdisk_cmd.append(f"{part_info.order}::+{part_info.size_in_gb}G")

    # Append ramdisk dev to the end for the sgdisk command
    sgdisk_cmd.append(RAMDISK_DEV)

    # Partition Ramdisk
    subprocess.run(sgdisk_cmd)


def format_partitions(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
    """
    Format each partition on the RAM disk with the specified filesystem type.

    Args:
        all_ramdisk_partitions (AllRamdiskPartInfo): An object containing partition information for the RAM disk.

    Returns:
        None
    """
    for part_info in all_ramdisk_partitions:
        subprocess.run([f"/usr/sbin/mkfs.{part_info.fstype}", f"{RAMDISK_DEV}p{part_info.order}"])


def mount_partitions(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
    """
    Mount each partition of the RAM disk to the specified destination.

    Args:
        all_ramdisk_partitions (AllRamdiskPartInfo): An object containing partition information for the RAM disk.

    Returns:
        None
    """
    for part_info in all_ramdisk_partitions:
        # Determine source and dest
        mount_src = f"{RAMDISK_DEV}p{part_info.order}"
        mount_dest = os.path.join(RAMDISK_BASE, part_info.destination.lstrip("/"))

        # Create dest if it doesn't exist
        os.makedirs(mount_dest, exist_ok=True)

        subprocess.run(["mount", mount_src, mount_dest])


def create_ramdisk_partitions(physical_mounts: AllMounts) -> AllRamdiskPartInfo:
    """
    Create partition information for the RAM disk based on physical mounts.

    Args:
        physical_mounts (AllMounts): An object containing all the physical mounts.

    Returns:
        AllRamdiskPartInfo: An object containing partition information for the RAM disk.
    """
    ramdisk_partitions = []

    # Using enumerate, since multiple items at the same depth with different partition sizes may exist
    for idx, mount in enumerate(physical_mounts, start=1):
        ramdisk_partitions.append(RamdiskPartInfo.create_ramdisk_part_info(mount, order=idx))

    return AllRamdiskPartInfo(ramdisk_partitions)


def simple_ramdisk(size_in_gb: int, fstype: str) -> str:
    """
    Create a simple RAM disk with a single partition and specified filesystem type.

    Args:
        size_in_gb (int): The size of the RAM disk in gigabytes.
        fstype (str): The filesystem type to format the RAM disk partition with.

    Returns:
        str: The base path of the RAM disk.
    """
    part_info = AllRamdiskPartInfo(
        [RamdiskPartInfo(size_in_gb=size_in_gb, destination="/", order=1, fstype=fstype)]
    )

    return create_ramdisk_worker(part_info)


def create_ramdisk_worker(all_ramdisk_partitions: AllRamdiskPartInfo) -> str:
    """
    Create, partition, format, and mount the RAM disk according to the specified partitions.

    Args:
        all_ramdisk_partitions (AllRamdiskPartInfo): An object containing partition information for the RAM disk.

    Returns:
        str: The base path of the RAM disk.
    """
    # Create the Ramdisk, specifying the number of partitions and the total size
    total_ramdisk_size = sum(part_info.size_in_gb for part_info in all_ramdisk_partitions)

    # Adding a small amount of buffer to handle issues with assuming that all partition sizes are ints
    # Min of 2GB, max of 5%
    total_ramdisk_size += max(2, int(total_ramdisk_size * 0.05))

    # Create the block device
    modprobe_ramdisk(total_ramdisk_size, len(all_ramdisk_partitions))

    # Partition the block device
    partition_ramdisk(all_ramdisk_partitions)

    # Format the new partitions
    format_partitions(all_ramdisk_partitions)

    # Mount the new partitions
    mount_partitions(all_ramdisk_partitions)

    return RAMDISK_BASE


def get_simple_ramdisk_size(physical_mounts: AllMounts) -> int:
    """
    Determine the size of the simple RAM disk based on the configuration or physical mounts.

    Args:
        physical_mounts (AllMounts): An object containing all the physical mounts.

    Returns:
        int: The size of the simple RAM disk in gigabytes.
    """
    config_size = RambootConfig.get_simple_ramdisk_size_gb()

    if config_size is not None:
        return config_size

    # Create a dictionary of parent_disks to parent_disk_size_gb
    # Making sure that we don't count the same parent_disk combination multiple times
    # Worst case, we end up inflating the size more than needed if we have some kind of weird striping
    # i.e. sda - sdb and sdb - sdc would be considered different parent disks
    parent_disks_to_size_dict = {tuple(mount.get_parent_disks()): mount.get_parent_size_gb() for mount in
                                 physical_mounts if mount.get_parent_disks() is not None}

    # Get the sum of the parent_gb_sizes
    return sum(val for val in parent_disks_to_size_dict.values())


def get_simple_ramdisk_fstype(root_mount: MountInfo) -> str:
    """
    Determine the filesystem type for the simple RAM disk based on the configuration or root mount.

    Args:
        root_mount (MountInfo): The root mount information.

    Returns:
        str: The filesystem type for the simple RAM disk.
    """
    config_fstype = RambootConfig.get_simple_ramdisk_fstype()

    if config_fstype is not None:
        return config_fstype

    return root_mount.fstype


def create_ramdisk(physical_mounts: AllMounts) -> str:
    """
    Create the RAM disk based on the configuration or physical mounts.

    Args:
        physical_mounts (AllMounts): An object containing all the physical mounts.

    Returns:
        str: The base path of the RAM disk.
    """
    root_mount = physical_mounts.get_root_mount()

    # Check if single partition is requested or fstype is btrfs
    # btrfs has subvolumes which act weirdly, easier to assume a single partition
    # zfs uses volumes as well, easier to assume a single partition
    if RambootConfig.get_use_simple_ramdisk() or root_mount.fstype in {"zfs", "btrfs"}:
        ramdisk_size = get_simple_ramdisk_size(physical_mounts)
        ramdisk_fstype = get_simple_ramdisk_fstype(root_mount)

        return simple_ramdisk(ramdisk_size, ramdisk_fstype)

    # Otherwise, keep going with more complex partitioning
    else:
        all_ramdisk_partitions = create_ramdisk_partitions(physical_mounts)
        return create_ramdisk_worker(all_ramdisk_partitions)
