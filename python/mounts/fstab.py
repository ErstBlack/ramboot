import os
from concurrent.futures import ThreadPoolExecutor
from typing import List
from mounts.mount_info import MountInfo, AllMounts
from mounts.mounts import check_for_ignored_mounts
from utils.rambootconfig import RambootConfig


def read_fstab(fstab_file: str) -> List[str]:
    with open(fstab_file, "r") as f:
        return f.readlines()


def cleanup_fstab(fstab_lines: List[str]):
    clean_lines = (line for line in fstab_lines if line.strip())
    clean_lines = (line for line in clean_lines if not line.startswith("#") and len(line.strip()))

    return list(clean_lines)


def get_mounts() -> List[MountInfo]:
    fstab = cleanup_fstab(read_fstab(RambootConfig.get_fstab_file()))

    mount_points = [MountInfo.create_mount_info(line) for line in fstab]
    mount_points = check_for_ignored_mounts(mount_points)

    return mount_points


def get_all_mounts_fast() -> List[MountInfo]:
    fstab = RambootConfig.get_fstab_file()
    with ThreadPoolExecutor() as pool:
        mount_points = pool.map(MountInfo.create_mount_info, fstab)

    return list(mount_points)


def replace_fstab(all_mounts: AllMounts, ramdisk_base: str) -> None:
    fstab_path = os.path.join(ramdisk_base, RambootConfig.get_fstab_file())
    fstab_lines = [mount.to_fstab_line() for mount in all_mounts if not mount.is_physical()]

    with open(fstab_path, "w") as f:
        f.writelines(line + os.linesep for line in fstab_lines)
