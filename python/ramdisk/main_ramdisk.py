import os
import subprocess

from ramdisk.ramdisk_part_info import AllRamdiskPartInfo, RamdiskPartInfo
from mounts.mount_info import AllMounts

RAMDISK_DEV = "/dev/ram0"
RAMDISK_BASE = "/mnt/ramdisk-ramboot"


def modprobe_ramdisk(size_in_gb: int, num_partitions: int) -> None:
    # Create the Ramdisk, specifying the number of partitions and the total size
    modprobe_cmd = ["/usr/sbin/modprobe", "brd", "rd_nr=1", f"max_part={num_partitions}",
                    f"rd_size={1024 * 1024 * size_in_gb}"]

    subprocess.run(modprobe_cmd)


def partition_ramdisk(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
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
    for part_info in all_ramdisk_partitions:
        subprocess.run([f"/usr/sbin/mkfs.{part_info.fstype}", f"{RAMDISK_DEV}p{part_info.order}"])


def mount_partitions(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
    for part_info in all_ramdisk_partitions:
        # Determine source and dest
        mount_src = f"{RAMDISK_DEV}p{part_info.order}"
        mount_dest = os.path.join(RAMDISK_BASE, part_info.destination.lstrip("/"))

        # Create dest if it doesn't exist
        os.makedirs(mount_dest, exist_ok=True)

        subprocess.run(["mount", mount_src, mount_dest])


def create_ramdisk_partitions(physical_mounts: AllMounts) -> AllRamdiskPartInfo:
    ramdisk_partitions = []

    # Using enumerate, since multiple items at the same depth with different partition sizes may exist
    for idx, mount in enumerate(physical_mounts, start=1):
        ramdisk_partitions.append(RamdiskPartInfo.create_ramdisk_part_info(mount, order=idx))

    return AllRamdiskPartInfo(ramdisk_partitions)


def simple_ramdisk(size_in_gb: int, fstype: str) -> str:
    part_info = AllRamdiskPartInfo(
        [RamdiskPartInfo(size_in_gb=size_in_gb, destination="/", order=1, fstype=fstype)])

    return create_ramdisk_worker(part_info)


def create_ramdisk_worker(all_ramdisk_partitions: AllRamdiskPartInfo) -> str:
    # Figure out the total size of the disk
    total_ramdisk_size = sum(part_info.size_in_gb for part_info in all_ramdisk_partitions)

    # Add a small buffer
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


def create_ramdisk(physical_mounts: AllMounts, simple_ramdisk_boot=True) -> str:
    # Get Root for quick checks
    root_mount = physical_mounts.get_root_mount()

    # Check if single partition is requested or fstype is btrfs
    # btrfs has subvolumes which act weirdly, easier to assume a single partition
    if simple_ramdisk_boot or root_mount.fstype == "btrfs":

        # If we have a raid, we need to sum up the total partitions
        if any(mount.is_raid() for mount in physical_mounts):
            ramdisk_size = sum(mount.get_size_gb() for mount in physical_mounts)
            simple_ramdisk(ramdisk_size, root_mount.fstype)

        # Otherwise we can get it from the size of the disk that root is on
        return simple_ramdisk(root_mount.get_parent_size_gb(), root_mount.fstype)

    # Otherwise, keep going with more complex partitioning
    else:
        all_ramdisk_partitions = create_ramdisk_partitions(physical_mounts)
        return create_ramdisk_worker(all_ramdisk_partitions)
