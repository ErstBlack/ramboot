import os
import shutil
import subprocess
import tempfile

from regular_part.mounts.mount_info import MountInfo, AllMounts

COPY_CMD = ["cp", "--archive", "--one-file-system"]


def mount_source(mount_src: MountInfo, temp_mount_point: str) -> None:
    # Mount to temp_mount_point
    subprocess.run(["mount", mount_src.partition, temp_mount_point])


def unmount_source(mount_point: str) -> None:
    # Unmount from temp_mount_point
    subprocess.run(["umount", mount_point])


def copy_mount(mount: MountInfo, ramdisk_base: str) -> None:
    # Make sure ramdisk destination exists
    ramdisk_copy_point = os.path.join(ramdisk_base, mount.dest.lstrip('/'))
    os.makedirs(ramdisk_copy_point, exist_ok=True)

    # Delete ramdisk copy point to prevent naming issues
    # i.e. /var/tmp -> /var so tmp can be copied properly
    shutil.rmtree(ramdisk_copy_point)

    with tempfile.TemporaryDirectory() as temp_mount_point:
        # Mount source
        mount_source(mount, temp_mount_point)

        # Copy from temp mount to ramdisk point
        subprocess.run(COPY_CMD + [temp_mount_point, ramdisk_copy_point])

        # Unmount Source
        unmount_source(temp_mount_point)


def copy_root_mount(ramdisk_base: str) -> None:
    # Copy from temp mount to ramdisk point
    subprocess.run(COPY_CMD + ["/", ramdisk_base])


def copy_all_mounts(all_mounts: AllMounts, ramdisk_base: str) -> None:
    for mount in all_mounts:
        # Root is a special case
        if mount.dest == "/":
            copy_root_mount(ramdisk_base)
        else:
            copy_mount(mount, ramdisk_base)
