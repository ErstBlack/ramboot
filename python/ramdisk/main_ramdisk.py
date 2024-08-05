import os
import subprocess


def create_ramdisk_simple(size_in_gb, fstype="xfs") -> str:
    subprocess.run(["/sbin/modprobe", "brd", "rd_nr=1", f"rd_size={1024 * 1024 * size_in_gb}"])
    subprocess.run([f"/sbin/mkfs.{fstype}", "-f", "/dev/ram0"])

    return "/dev/ram0"


def mount_ramdisk_partition(partition: str, target: str) -> None:
    os.makedirs(target, exist_ok=True)
    subprocess.run(["mount", partition, target])


def simple_ramdisk(size_in_gb, fstype="xfs") -> str:
    ramdisk_mount = "/mnt/ramdisk-ramboot"

    ramdisk_dev = create_ramdisk_simple(size_in_gb, fstype)
    mount_ramdisk_partition(ramdisk_dev, ramdisk_mount)

    return ramdisk_mount
