## Build
1. Install required OS packages, the example below is for a Centos based distro
   1. `dnf install --assumeyes python38 python38-devel python38-pip python38-setuptools python38-wheel zlib-devel git`
2. Install required Python packages.  You may also need to upgrade pip, setuptools, and/or wheel
   1. `python3.8 -m pip install --upgrade pyinstaller`
3. Clone the repo
   1. `git clone https://github.com/ErstBlack/ramboot.git`
4. Use Pyinstaller to create the binary
   1. `cd ./ramboot && pyinstaller --onefile ramboot.py`
5. The binary will be at `dist/ramboot`

## Installation

1. Download/Build `ramboot` and `ramboot.sh`
2. Create `/usr/sbin/ramboot/` and move `ramboot` and `ramboot.sh` inside
3. Update grub to point the `init` process at `ramboot.sh`, see below for an example of how to do this
   1. `grubby --update-kernel=all --args='init=/usr/sbin/ramboot/ramboot.sh'`
   2. `grub2-mkconfig --output /boot/efi/EFI/rocky/grub.cfg`

## Configuration

The application uses an INI configuration file.  By default, it looks for this file at `/etc/ramboot.conf`.

If the file does not exist, default values are used.

```ini
[main]
simple_ramdisk = true  ; Use a simple RAM disk (default: true)
hide_disks = false     ; Hide physical disks (default: false)

[ramdisk_simple]
size_gb = 4            ; Size of the simple RAM disk in gigabytes (default: None)
fstype = ext4          ; Filesystem type for the simple RAM disk (default: None)
zfs_replacement_fstype = ext4  ; Fallback filesystem if ZFS is used for root (default: ext4)

[activations]
raid = true            ; Whether or not to check for/activate software raid(s) (default: true)
zfs = true             ; Whether or not to check for/activate zpool(s) (default: true)
btrfs = true           ; Whether or not to check for/activate btrfs volume(s) (default: true)
lvm = true             ; Whether or not to check for/activate lv(s) (default: true)

[mounts]
ignored_mounts = ["mount1", "mount2"]  ; List of mount points to ignore (default: [])
fstab_file = /etc/fstab  ; Path to the fstab file (default: /etc/fstab)
```

## Limitations

- Currently, the application has been tested on the following OS - Filesystem - Partitioning Schema combinations.

| Operating System   | Filesystem | Partitioning              |
|--------------------|------------|---------------------------|
| Ubuntu 20.04       | EXT4       | Standard                  |
| Ubuntu 20.04       | EXT4       | LVM                       |
| Ubuntu 20.04       | EXT4       | LVM (with LUKS)           |
| Ubuntu 20.04       | ZFS        | ZFS                       |
| RockyLinux 9.4     | XFS        | RAID 1 (4 disks)          |
| RockyLinux 9.4     | XFS        | RAID 1 with LVM (4 disks) |
| OpenSUSE LEAP 15.6 | BTRFS      | BTRFS                     |

- The Ramboot binary was built on a RockyLinux:8 container with GLIBC 2.28.
- The application currently assumes that systemd is used as the init system.
