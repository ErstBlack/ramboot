import os
import shutil
import subprocess
import tempfile

from regular_part.mounts.all_mounts import AllMounts
from regular_part.mounts.mount_info import MountInfo

COPY_CMD = ["cp", "--archive", "--one-file-system"]


def mount_source(mount: MountInfo) -> str:
    # Create temp mount point
    temp_mount_point = tempfile.mkdtemp()
    subprocess.run(["mount", mount.partition, temp_mount_point])

    return temp_mount_point


def unmount_source(mount_point: str)-> None:
    subprocess.run(["umount", mount_point])
    shutil.rmtree(mount_point)


def copy_mount(mount: MountInfo, ramdisk_base: str)-> None:
    # Create Ramdisk destination
    ramdisk_copy_point = os.path.join(ramdisk_base, mount.dest.lstrip('/'))
    os.makedirs(ramdisk_copy_point, exist_ok=True)

    # Delete ramdisk copy point to prevent naming issues
    shutil.rmtree(ramdisk_copy_point)

    # Mount source
    temp_mount_point = mount_source(mount)

    # Copy from temp mount to ramdisk point
    subprocess.run(COPY_CMD + [temp_mount_point, ramdisk_copy_point])

    # Unmount Source
    unmount_source(temp_mount_point)


def copy_root_mount(ramdisk_base: str)-> None:
    # Copy from temp mount to ramdisk point
    subprocess.run(COPY_CMD + ["/", ramdisk_base])


def copy_all_mounts(all_mounts: AllMounts, ramdisk_base: str)-> None:
    for mount in all_mounts:
        # Root is a special case
        if mount.dest == "/":
            copy_root_mount(ramdisk_base)
        else:
            copy_mount(mount, ramdisk_base)
