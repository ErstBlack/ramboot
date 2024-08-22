import os
import subprocess
import tempfile

from setup.mounts.mount_info import MountInfo, AllMounts

COPY_CMD = ["cp", "--archive", "--one-file-system"]


def create_copy_point(mount: MountInfo, ramdisk_base: str) -> str:
    """
    Create a copy destination directory on the RAM disk for a given mount point.

    This function ensures that the target directory on the RAM disk where the contents of
    the mount point will be copied exists. If the directory doesn't exist, it is created.

    Args:
        mount (MountInfo): The mount point information that needs to be copied.
        ramdisk_base (str): The base directory on the RAM disk where the contents should be copied.

    Returns:
        str: The path to the created directory on the RAM disk.
    """
    ramdisk_copy_point = os.path.join(ramdisk_base, mount.dest.lstrip('/'))
    os.makedirs(ramdisk_copy_point, exist_ok=True)

    return ramdisk_copy_point


def mount_source(mount: MountInfo) -> str:
    """
    Mount the source filesystem to a temporary directory for copying.

    This function mounts the source filesystem to a temporary mount point, handling
    special cases for `btrfs` and `zfs` filesystems.

    Args:
        mount (MountInfo): The mount point information that needs to be mounted temporarily.

    Returns:
        str: The path to the temporary mount point.
    """
    # Create Source Mount Point
    temp_mount_point = tempfile.mkdtemp()

    # If we have a btrfs, we need to handle subvols
    if mount.fstype == "btrfs":
        subprocess.run(["mount", "--options", ",".join(mount.fsopts), mount.source, temp_mount_point])

    # If we have a zfs, we need to handle volumes via zfsutil
    elif mount.fstype == "zfs":
        subprocess.run(["mount", "--types", "zfs", "--options", "zfsutil", mount.source, temp_mount_point])

    # Otherwise, mount normally
    else:
        subprocess.run(["mount", mount.source, temp_mount_point])

    return temp_mount_point


def copy_from_source(temp_mount_point: str, ramdisk_copy_point: str) -> None:
    """
    Copy the contents of the source mount point to the RAM disk.

    This function copies the contents of the mounted source filesystem to the destination
    directory on the RAM disk. It ensures that the copying process behaves as expected
    by appending `/.` to the source path.

    Args:
        temp_mount_point (str): The path to the temporary mount point.
        ramdisk_copy_point (str): The path to the destination directory on the RAM disk.

    Returns:
        None
    """
    # cp behaves weirdly when you copy to an existing directory, adding /. to the end gives us the behavior we want
    copy_temp_mount_point = f"{temp_mount_point}{os.path.sep}."
    subprocess.run(COPY_CMD + [copy_temp_mount_point, ramdisk_copy_point])


def cleanup_mount(temp_mount_point: str) -> None:
    """
    Unmount and clean up the temporary mount point.

    This function unmounts the source filesystem from the temporary mount point and
    then removes the temporary directory.

    Args:
        temp_mount_point (str): The path to the temporary mount point.

    Returns:
        None
    """
    # Unmount Source
    subprocess.run(["umount", "--force", temp_mount_point])

    # Cleanup Source
    os.rmdir(temp_mount_point)


def copy_mount(mount: MountInfo, ramdisk_base: str) -> None:
    """
    Copy the contents of a specific mount point to the RAM disk.

    This function manages the entire process of copying a mount point to the RAM disk.
    It creates the destination directory, mounts the source, copies the contents,
    and then cleans up the temporary resources.

    Args:
        mount (MountInfo): The mount point information to be copied.
        ramdisk_base (str): The base directory on the RAM disk.

    Returns:
        None
    """
    # Make sure ramdisk destination exists
    ramdisk_copy_point = create_copy_point(mount, ramdisk_base)

    # Mount source to temporary mount point
    temp_mount_point = mount_source(mount)

    # Copy from temp mount to ramdisk point
    copy_from_source(temp_mount_point, ramdisk_copy_point)

    # Unmount and remove temporary mount point
    cleanup_mount(temp_mount_point)


def copy_root_mount(ramdisk_base: str) -> None:
    """
    Copy the root filesystem to the RAM disk.

    This function copies the contents of the root filesystem (`/`) to the RAM disk.
    It uses the `cp` command to perform an archive copy, ensuring that all files
    and directories are replicated.

    Args:
        ramdisk_base (str): The base directory on the RAM disk.

    Returns:
        None
    """
    subprocess.run(COPY_CMD + ["/.", ramdisk_base])


def copy_all_mounts(all_mounts: AllMounts, ramdisk_base: str) -> None:
    """
    Copy all mounted filesystems to the RAM disk.

    This function iterates through all the mount points and copies each one to the RAM disk.

    Args:
        all_mounts (AllMounts): A collection of all mount point information.
        ramdisk_base (str): The base directory on the RAM disk.

    Returns:
        None
    """
    for mount in all_mounts:
        # Root is a special case
        if mount.dest == "/":
            copy_root_mount(ramdisk_base)
        else:
            copy_mount(mount, ramdisk_base)
