from __future__ import annotations

import configparser
import json
import os


class RambootConfig:
    """
    A class to handle the configuration for the Ramboot service.

    This class provides various class methods to retrieve configuration
    settings from the Ramboot configuration file.

    Attributes:
        _config (ConfigParser): A ConfigParser object that holds the configuration
            data read from the configuration file.
    """

    _config = configparser.ConfigParser()
    _config.read(os.getenv("RAMBOOT_CONFIG", "/etc/ramboot.conf"))

    @classmethod
    def get_config(cls):
        """
        Retrieve the entire configuration object.

        Returns:
            ConfigParser: The ConfigParser object representing the config file..
        """
        return cls._config

    @classmethod
    def get_use_simple_ramdisk(cls) -> bool:
        """
        Check if a simple RAM disk should be used.

        Returns:
            bool: True if a simple RAM disk should be used, False otherwise.  Defaults to True.
        """
        return cls._config.getboolean("main", "simple_ramdisk", fallback=True)

    @classmethod
    def get_hide_disks(cls) -> bool:
        """
        Check if disks should be hidden.

        Returns:
            bool: True if disks should be hidden, defaulting to False.
        """
        return cls._config.getboolean("main", "hide_disks", fallback=False)

    @classmethod
    def get_simple_ramdisk_size_gb(cls) -> int | None:
        """
        Get the size of the simple RAM disk in gigabytes.

        Returns:
            int | None: The size of the simple RAM disk in gigabytes, defaulting to None.
        """
        return cls._config.getint("ramdisk_simple", "size_gb", fallback=None)

    @classmethod
    def get_simple_ramdisk_fstype(cls) -> str | None:
        """
        Get the filesystem type of the simple RAM disk.

        Returns:
            str | None: The filesystem type of the simple RAM disk, defaulting to None.
        """
        return cls._config.get("ramdisk_simple", "fstype", fallback=None)

    @classmethod
    def get_activate_field(cls, field: str) -> str:
        """
        Retrieve the value of a specific activation field.

        Args:
            field (str): The name of the activation field to retrieve.

        Returns:
            str: The value of the specified activation field, defaulting to True.
        """
        return cls._config.get("activations", field, fallback=True)

    @classmethod
    def get_ignored_mounts(cls) -> set:
        """
        Get the set of ignored mounts.

        Returns:
            set: A set of ignored mount points, defaulting to an empty set.
        """
        return set(json.loads(cls._config.get("mounts", "ignored_mounts", fallback="[]")))

    @classmethod
    def get_fstab_file(cls):
        """
        Get the path to the fstab file.

        Returns:
            str: The path to the fstab file, defaulting to /etc/fstab.
        """
        return cls._config.get("mounts", "fstab_file", fallback="/etc/fstab")

    @classmethod
    def get_zfs_alternative_ramdisk_fstype(cls) -> str:
        """
        Get the alternative filesystem type to be used if ZFS is not available for the RAM disk.

        Returns:
            str: The alternative filesystem type, defaulting to "ext4".
        """
        return cls._config.get("ramdisk_simple", "zfs_replacement_fstype", fallback="ext4")
