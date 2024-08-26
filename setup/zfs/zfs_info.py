from __future__ import annotations

import itertools
import math
import shlex
from typing import List
from collections import defaultdict
from collections.abc import Sequence

from setup.mounts.mount_info import MountInfo
from utils.shell_commands import check_output_wrapper, get_disk_size, get_device_disks


class ZfsInfo:
    SIZE_CMD = ["/usr/sbin/zpool", "list", "-H", "-o", "size", "-p"]

    def __init__(self, zfs_vol: str, order: int):
        # Using shlex since values could be surrounded by quotes in theory
        name, dest = shlex.split(zfs_vol)

        # Base values that we need
        self.name: str = name
        self.dest: str = dest
        self.order: int = order

        # Derived Values
        self._pool: str | None = None
        self._size_gb: int | None = None
        self._partitions: List[str] | None = None
        self._parent_disks: List[str] | None = None
        self._parent_size_gb: int | None = None

        # Figure out values
        self._pool = self.get_pool()
        self._size_gb = self.get_size_gb()
        self._partitions = self.get_partitions()
        self._parent_disks = self.get_parent_disks()
        self._parent_size_gb = self.get_parent_size_gb()

    def get_pool(self) -> str:
        if self._pool:
            return self._pool

        return self.name.split("/")[0]

    def get_partitions(self) -> List[str]:
        if self._partitions is not None:
            return self._partitions

        zpool_list_cmd = ["zpool", "status", "-L", "-P"]

        # Get the result, split on newline and remove leading and trailing spaces
        output = check_output_wrapper(zpool_list_cmd + [self.get_pool()])
        lines = [line.strip() for line in output.split("\n")]

        # Lines we care about start with partition
        # e.g. /dev/sda3
        return [line.split()[0] for line in lines if line.startswith("/dev")]

    def get_parent_disks(self) -> List[str]:
        if self._parent_disks is not None:
            return self._parent_disks

        if self._partitions is not None and len(self._partitions):
            # Get disks from the partitions, then flatten list and remove duplicates
            disks = set(itertools.chain.from_iterable(get_device_disks(device) for device in self._partitions))

            return sorted(disks)

    def get_size_gb(self) -> int:
        if self._size_gb:
            return self._size_gb

        if self._pool is not None:
            size_in_bytes = check_output_wrapper(ZfsInfo.SIZE_CMD + [self._pool])

            # Convert from bytes to GB
            return math.ceil(float(size_in_bytes) / 1024 ** 3)

    def get_parent_size_gb(self) -> int:
        if self._parent_size_gb:
            return self._parent_size_gb

        if self._parent_disks is not None and len(self._parent_disks):
            # Assuming a normal type of raid that is based off of the smallest disk in the system
            size_in_bytes = min(get_disk_size(disk) for disk in self._parent_disks)

            # Convert from bytes to GB
            return math.ceil(float(size_in_bytes) / 1024 ** 3)

    def to_mount_info(self) -> MountInfo:
        mount = MountInfo(self.name, self.dest, "zfs", [], "0", "0")
        mount._is_lvm = False
        mount._size_gb = self.get_size_gb()
        mount._partitions = self.get_partitions()
        mount._parent_disks = self.get_parent_disks()
        mount._parent_size_gb = self.get_parent_size_gb()
        mount._initialized = True

        return mount


class AllZfs(Sequence):
    def __init__(self, zfs_list: List[ZfsInfo]):
        self.zfs_list: List[ZfsInfo] = zfs_list

        self._remove_none_mounts()
        self._remove_duplicates()

    def __next__(self) -> ZfsInfo:
        """Implement the iterator protocol for AllMounts.

        Returns:
            MountInfo: The next MountInfo object in the sequence.
        """
        for zfs_info in self.zfs_list:
            yield zfs_info

    def __len__(self) -> int:
        """Get the number of mounts in this collection.

        Returns:
            int: The number of mounts.
        """
        return len(self.zfs_list)

    def __getitem__(self, item) -> ZfsInfo:
        """Get a specific MountInfo object by index.

        Args:
            item: The index of the desired MountInfo object.

        Returns:
            MountInfo: The MountInfo object at the specified index.
        """
        return self.zfs_list[item]

    def _remove_none_mounts(self):
        new_zfs_list = []
        for zfs_vol in self.zfs_list:
            # Remove any values that don't have mount points
            if zfs_vol.dest != "none":
                new_zfs_list.append(zfs_vol)

        self.zfs_list = new_zfs_list

    def _remove_duplicates(self):
        zfs_dict = defaultdict(list)

        # Organize the zfs volumes by their dest
        for zfs_vol in self.zfs_list:
            zfs_dict[zfs_vol.dest].append(zfs_vol)

        new_zfs_vols = []

        for key, val in zfs_dict.items():
            # Sort by order found in zfs list, taking the last value found
            new_zfs_vols.append(sorted(val, key=lambda zvol: zvol.order)[-1])

        self.zfs_list = new_zfs_vols
