from __future__ import annotations

import configparser
import json
import os


class RambootConfig:
    _config = configparser.ConfigParser()
    _config.read(os.getenv("RAMBOOT_CONFIG", "/etc/ramboot.conf"))

    @classmethod
    def get_config(cls):
        return cls._config

    @classmethod
    def get_use_simple_ramdisk(cls) -> bool:
        return cls._config.getboolean("main", "simple_ramdisk", fallback=True)

    @classmethod
    def get_hide_disks(cls) -> bool:
        return cls._config.getboolean("main", "hide_disks", fallback=False)

    @classmethod
    def get_simple_ramdisk_size_gb(cls) -> int | None:
        return cls._config.getint("ramdisk_simple", "size_gb", fallback=None)

    @classmethod
    def get_simple_ramdisk_fstype(cls) -> str | None:
        return cls._config.get("ramdisk_simple", "fstype", fallback=None)

    @classmethod
    def get_activate_field(cls, field: str) -> str:
        return cls._config.get("activations", field, fallback=True)

    @classmethod
    def get_ignored_mounts(cls) -> set:
        return set(json.loads(cls._config.get("mounts", "ignored_mounts", fallback="[]")))

    @classmethod
    def get_fstab_file(cls):
        return cls._config.get("mounts", "fstab_file", fallback="/etc/fstab")

    @classmethod
    def get_zfs_alternative_ramdisk_fstype(cls) -> str:
        return cls._config.get("ramdisk_simple", "zfs_replacement_fstype", fallback="ext4")