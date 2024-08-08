import os

from regular_part.mounts.all_mounts import AllMounts


def overwrite_fstab(fstab_lines, fstab_path) -> None:
    with open(fstab_path, "w") as f:
        f.writelines(line + os.linesep for line in fstab_lines)


def replace_fstab(all_mounts: AllMounts, ramdisk_base: str) -> None:
    fstab_path = os.path.join(ramdisk_base, "etc/fstab")
    fstab_lines = []

    for mount in all_mounts:
        if mount.is_physical() or mount.fstype == "swap":
            continue
        else:
            fstab_lines.append(mount.to_fstab_line())

    overwrite_fstab(fstab_lines, fstab_path)
