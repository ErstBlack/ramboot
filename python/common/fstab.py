from typing import List

from regular_part.mounts.mount_info import MountInfo

FSTAB_FILE = "/etc/fstab"


def read_fstab(fstab_file: str) -> List[str]:
    with open(FSTAB_FILE, "r") as f:
        return f.readlines()


def cleanup_fstab(fstab_lines: List[str]):
    clean_lines = (line for line in fstab_lines if line.strip())
    clean_lines = (line for line in clean_lines if not line.startswith("#") and len(line.strip()))

    return list(clean_lines)


def get_fstab(fstab_file=FSTAB_FILE) -> List[str]:
    return cleanup_fstab(read_fstab(fstab_file))


def get_all_mounts() -> List[MountInfo]:
    fstab = get_fstab()
    mount_points = [MountInfo.create_mount_info(line) for line in fstab]

    return mount_points
