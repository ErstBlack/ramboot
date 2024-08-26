import math
import shlex
from typing import List
from collections import defaultdict
from collections.abc import Sequence

from setup.mounts.mount_info import MountInfo
from utils.shell_commands import check_output_wrapper


class ZfsInfo:
    SIZE_CMD = ["/usr/sbin/zpool", "list", "-H", "-o", "size", "-p"]

    def __init__(self, zfs_vol: str, order: int):
        # Using shlex since values could be surrounded by quotes in theory
        name, dest = shlex.split(zfs_vol)

        # Base values that we need
        self.name = name
        self.dest = dest
        self.order = order

        # Derived Values
        self._pool = None
        self._size_gb = None

        # Figure out values
        self._pool = self.get_pool()
        self._size_gb = self.get_size_gb()

    def get_pool(self) -> List[str]:
        if self._pool:
            return self._pool

        return [self.name.split("/")[0]]

    def get_size_gb(self) -> int:
        if self._size_gb:
            return self._size_gb

        if self._pool is not None:
            size_in_bytes = check_output_wrapper(ZfsInfo.SIZE_CMD + [self._pool])

            # Convert from bytes to GB
            return math.ceil(float(size_in_bytes) / 1024 ** 3)

    def to_mount_info(self) -> MountInfo:
        mount = MountInfo(self.name, self.dest, "zfs", [], "0", "0")
        mount._is_lvm = False
        mount._is_raid = False
        # TODO: Create a get_partitions function to get partitions from zpool list -LP
        mount._partitions = [self.name]
        mount._size_gb = self.get_size_gb()
        # TODO: Create a get_parent_disks function to get partitions from list of partitions
        mount._parent_disks = self.get_pool()
        mount._parent_size_gb = self.get_size_gb()
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
