import os
import subprocess

OLD_ROOT = "oldroot"


def pivot_root(ramdisk_base: str) -> None:
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
