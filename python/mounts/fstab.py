import os
from concurrent.futures import ThreadPoolExecutor
from typing import List
from mounts.mount_info import MountInfo, AllMounts

FSTAB_FILE = "/etc/fstab"


def read_fstab(fstab_file: str) -> List[str]:
    with open(fstab_file, "r") as f:
        return f.readlines()


def cleanup_fstab(fstab_lines: List[str]):
    clean_lines = (line for line in fstab_lines if line.strip())
    clean_lines = (line for line in clean_lines if not line.startswith("#") and len(line.strip()))

    return list(clean_lines)


def get_fstab(fstab_file: str) -> List[str]:
    return cleanup_fstab(read_fstab(fstab_file))


def get_mounts() -> List[MountInfo]:
    fstab = get_fstab(FSTAB_FILE)
    mount_points = [MountInfo.create_mount_info(line) for line in fstab]

    return mount_points

def get_all_mounts_fast() -> List[MountInfo]:
    fstab = get_fstab(FSTAB_FILE)
    with ThreadPoolExecutor() as pool:
        mount_points = pool.map(MountInfo.create_mount_info, fstab)

    return list(mount_points)


def replace_fstab(all_mounts: AllMounts, ramdisk_base: str) -> None:
    fstab_path = os.path.join(ramdisk_base, "etc/fstab")
    fstab_lines = []

    for mount in all_mounts:
        # Skip over mounts we already covered and swap since it's not needed
        if mount.is_physical() or mount.fstype == "swap":
            continue
        else:
            fstab_lines.append(mount.to_fstab_line())

    with open(fstab_path, "w") as f:
        f.writelines(line + os.linesep for line in fstab_lines)
