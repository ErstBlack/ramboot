import os
import subprocess

from ramdisk.ramdisk_part_info import AllRamdiskPartInfo, RamdiskPartInfo
from regular_part.mounts.mount_info import MountInfo, AllMounts

RAMDISK_DEV = "/dev/ram0"
RAMDISK_BASE = "/mnt/ramdisk-ramboot"


def modprobe_ramdisk(size_in_gb: int, num_partitions: int) -> None:
    # Create the Ramdisk, specifying the number of partitions and the total size
    modprobe_cmd = ["/sbin/modprobe", "brd", "rd_nr=1", f"max_part={num_partitions}",
                    f"rd_size={1024 * 1024 * size_in_gb}"]

    print(f"MODPROBE CMD: {modprobe_cmd}")
    subprocess.run(modprobe_cmd)


def partition_ramdisk(all_ramdisk_partitions: AllRamdiskPartInfo) -> None:
    sgdisk_cmd = ["/sbin/sgdisk", "--zap-all"]

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
        subprocess.run([f"/sbin/mkfs.{part_info.fstype}", f"{RAMDISK_DEV}p{part_info.order}"])


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
    for idx, mount in enumerate(physical_mounts):
        ramdisk_partitions.append(RamdiskPartInfo.create_ramdisk_part_info(mount, order=idx))

    return AllRamdiskPartInfo(ramdisk_partitions)


def simple_ramdisk(root_mount: MountInfo) -> str:
    part_info = AllRamdiskPartInfo([RamdiskPartInfo.create_ramdisk_part_info(root_mount)])

    return create_ramdisk(part_info)


def create_ramdisk(all_ramdisk_partitions: AllRamdiskPartInfo) -> str:
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
