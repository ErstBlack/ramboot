import os

from regular_part.mounts.mount_info import AllMounts


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
