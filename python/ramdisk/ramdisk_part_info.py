from __future__ import annotations

from collections.abc import Sequence
from typing import List

from setup.mounts.mount_info import MountInfo
from utils.ramboot_config import RambootConfig


class RamdiskPartInfo:
    """
    Represents a partition on a RAM disk.

    This class contains information about a specific partition on a RAM disk,
    including its size, destination mount point, order, and filesystem type.
    If the filesystem type is `zfs`, it automatically substitutes it with an
    alternative filesystem type.

    Attributes:
        size_in_gb (int): The size of the partition in gigabytes.
        destination (str): The mount point where the partition will be mounted.
        order (int): The order of the partition on the RAM disk.
        fstype (str): The filesystem type of the partition.
    """

    def __init__(self, size_in_gb: int, destination: str, order: int, fstype: str = "ext4"):
        """
        Initializes a RamdiskPartInfo object with specified parameters.

        Args:
            size_in_gb (int): The size of the partition in gigabytes.
            destination (str): The mount point where the partition will be mounted.
            order (int): The order of the partition on the RAM disk.
            fstype (str, optional): The filesystem type of the partition. Defaults to "ext4".
                If set to "zfs", it is replaced with an alternative filesystem type.

        Raises:
            None
        """
        self.size_in_gb = size_in_gb
        self.destination = destination
        self.order = order

        # zfs is not a valid partition format
        if fstype == "zfs":
            fstype = RambootConfig.get_zfs_alternative_ramdisk_fstype()

        self.fstype = fstype

    @classmethod
    def create_ramdisk_part_info(cls, mount_info: MountInfo, order: int) -> RamdiskPartInfo:
        """
        Creates a RamdiskPartInfo instance from a given MountInfo object.

        This class method generates a RamdiskPartInfo instance based on the
        information provided by a MountInfo object and a specified partition order.

        Args:
            mount_info (MountInfo): The MountInfo object containing mount details.
            order (int): The order of the partition on the RAM disk.

        Returns:
            RamdiskPartInfo: A new instance of RamdiskPartInfo.
        """
        return cls(mount_info.get_size_gb(), mount_info.dest, order, mount_info.fstype)


class AllRamdiskPartInfo(Sequence):
    """
    Represents a collection of RamdiskPartInfo objects.

    This class provides a sequence interface to a list of RamdiskPartInfo objects,
    allowing iteration, indexing, and length retrieval. The partitions are sorted
    by their order upon initialization.

    Attributes:
        ramdisk_part_infos (List[RamdiskPartInfo]): The list of RamdiskPartInfo objects.
    """

    def __init__(self, ramdisk_part_infos: List[RamdiskPartInfo]):
        """
        Initializes an AllRamdiskPartInfo object with a list of RamdiskPartInfo objects.

        The partitions are sorted by their order after initialization.

        Args:
            ramdisk_part_infos (List[RamdiskPartInfo]): The list of RamdiskPartInfo objects.

        Raises:
            None
        """
        self.ramdisk_part_infos: List[RamdiskPartInfo] = ramdisk_part_infos
        self._sort_by_order()

    def __next__(self) -> RamdiskPartInfo:
        """
        Provides a generator for iterating over the RamdiskPartInfo objects.

        Yields:
            RamdiskPartInfo: The next partition in the sequence.

        Raises:
            StopIteration: When the end of the sequence is reached.
        """
        for part_info in self.ramdisk_part_infos:
            yield part_info

    def __len__(self):
        """
        Returns the number of partitions in the sequence.

        Returns:
            int: The number of RamdiskPartInfo objects.
        """
        return len(self.ramdisk_part_infos)

    def __getitem__(self, item) -> RamdiskPartInfo:
        """
        Retrieves a partition by its index in the sequence.

        Args:
            item (int): The index of the partition to retrieve.

        Returns:
            RamdiskPartInfo: The partition at the specified index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self.ramdisk_part_infos[item]

    def _sort_by_order(self):
        """
        Sorts the list of RamdiskPartInfo objects by their order attribute.

        The sorting is done in-place and modifies the original list.

        Returns:
            None
        """
        self.ramdisk_part_infos = sorted(self.ramdisk_part_infos, key=lambda part_info: part_info.order)
