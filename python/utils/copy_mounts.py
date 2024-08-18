import os
import subprocess
import tempfile

from mounts.mount_info import MountInfo, AllMounts

COPY_CMD = ["cp", "--archive", "--one-file-system"]


def copy_mount(mount: MountInfo, ramdisk_base: str) -> None:
    # Make sure ramdisk destination exists
    ramdisk_copy_point = os.path.join(ramdisk_base, mount.dest.lstrip('/'))
    os.makedirs(ramdisk_copy_point, exist_ok=True)

    # Create Source Mount Point
    temp_mount_point = tempfile.mkdtemp()

    # If we have a btrfs, we need to handle it a bit specially
    if mount.fstype == "btrfs":
        subprocess.run(["mount", mount.source, "--options", ",".join(mount.fsopts), temp_mount_point])

    # Otherwise, mount normally
    else:
        subprocess.run(["mount", mount.source, temp_mount_point])

    # Copy from temp mount to ramdisk point
    # cp behaves weirdly when you copy to an existing directory, adding /. to the end gives us the behavior we want
    copy_temp_mount_point = f"{temp_mount_point}{os.path.sep}."
    subprocess.run(COPY_CMD + [copy_temp_mount_point, ramdisk_copy_point])

    # Unmount Source
    subprocess.run(["umount", "--force", temp_mount_point])

    # Cleanup Source
    os.rmdir(temp_mount_point)


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
