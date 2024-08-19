import os
import subprocess
import tempfile

from mounts.mount_info import MountInfo, AllMounts

COPY_CMD = ["cp", "--archive", "--one-file-system"]


def create_copy_point(mount: MountInfo, ramdisk_base: str) -> str:
    ramdisk_copy_point = os.path.join(ramdisk_base, mount.dest.lstrip('/'))
    os.makedirs(ramdisk_copy_point, exist_ok=True)

    return ramdisk_copy_point


def mount_source(mount: MountInfo) -> str:
    # Create Source Mount Point
    temp_mount_point = tempfile.mkdtemp()

    # If we have a btrfs, we need to handle subvols
    if mount.fstype == "btrfs":
        subprocess.run(["mount", "--options", ",".join(mount.fsopts), mount.source, temp_mount_point])

    # If we have a zfs, we need to handle volumes via zfsutil
    if mount.fstype == "zfs":
        subprocess.run(["mount", "--types", "zfs", "--options", "zfsutil", mount.source, temp_mount_point])

    # Otherwise, mount normally
    else:
        subprocess.run(["mount", mount.source, temp_mount_point])

    return temp_mount_point


def copy_from_source(temp_mount_point: str, ramdisk_copy_point: str) -> None:
    # cp behaves weirdly when you copy to an existing directory, adding /. to the end gives us the behavior we want
    copy_temp_mount_point = f"{temp_mount_point}{os.path.sep}."
    subprocess.run(COPY_CMD + [copy_temp_mount_point, ramdisk_copy_point])


def cleanup_mount(temp_mount_point: str) -> None:
    # Unmount Source
    subprocess.run(["umount", "--force", temp_mount_point])

    # Cleanup Source
    os.rmdir(temp_mount_point)


def copy_mount(mount: MountInfo, ramdisk_base: str) -> None:
    # Make sure ramdisk destination exists
    ramdisk_copy_point = create_copy_point(mount, ramdisk_base)

    # Mount source to temporary mount point
    temp_mount_point = mount_source(mount)

    # Copy from temp mount to ramdisk point
    copy_from_source(temp_mount_point, ramdisk_copy_point)

    # Unmount and remove temporary mount point
    cleanup_mount(temp_mount_point)


def copy_root_mount(ramdisk_base: str) -> None:
    # Copy from temp mount to ramdisk point
    subprocess.run(COPY_CMD + ["/.", ramdisk_base])


def copy_all_mounts(all_mounts: AllMounts, ramdisk_base: str) -> None:
    for mount in all_mounts:
        # Root is a special case
        if mount.dest == "/":
            copy_root_mount(ramdisk_base)
        else:
            copy_mount(mount, ramdisk_base)
