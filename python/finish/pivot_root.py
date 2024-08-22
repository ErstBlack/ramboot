import os
import subprocess

OLD_ROOT = "oldroot"


def pivot_root(ramdisk_base: str) -> None:
    """
        Pivot the root filesystem to a new location on the RAM disk.

        This function changes the root filesystem to the specified RAM disk base directory,
        effectively switching the system to run from the RAM disk. The previous root
        filesystem is moved to a subdirectory (`oldroot`) and unmounted.

        Args:
            ramdisk_base (str): The base directory on the RAM disk to which the root filesystem
                                should be pivoted.

        Returns:
            None
        """
    # Switch to ramdisk
    os.chdir(ramdisk_base)

    # Create oldroot
    os.mkdir(os.path.join(ramdisk_base, OLD_ROOT))

    # pivotroot
    subprocess.run(["./usr/sbin/pivot_root", ".", "oldroot"])

    # Unmount oldroot
    subprocess.run(["umount", "--lazy", "--recursive", OLD_ROOT])

    try:
        os.rmdir(OLD_ROOT)
    except OSError:
        pass
