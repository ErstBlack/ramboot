from __future__ import annotations

from collections.abc import Sequence
from typing import List

from mounts.mount_info import MountInfo


class RamdiskPartInfo:
    def __init__(self, size_in_gb: int, destination: str, order: int, fstype: str = "xfs"):
        self.size_in_gb = size_in_gb
        self.destination = destination
        self.order = order
        self.fstype = fstype
        self.lvm_tree = None

    @classmethod
    def create_ramdisk_part_info(cls, mount_info: MountInfo, order=None) -> RamdiskPartInfo:
        if order is None:
            return RamdiskPartInfo(mount_info.get_size_gb(), mount_info.dest, mount_info.get_dest_depth(), mount_info.fstype)
        else:
            return RamdiskPartInfo(mount_info.get_size_gb(), mount_info.dest, order, mount_info.fstype)


class AllRamdiskPartInfo(Sequence):
    def __init__(self, ramdisk_part_infos: List[RamdiskPartInfo]):
        self.ramdisk_part_infos: List[RamdiskPartInfo] = ramdisk_part_infos
        self._sort_by_order()

    def __next__(self) -> RamdiskPartInfo:
        for part_info in self.ramdisk_part_infos:
            yield part_info

    def __len__(self):
        return len(self.ramdisk_part_infos)

    def __getitem__(self, item) -> RamdiskPartInfo:
        return self.ramdisk_part_infos[item]

    def _sort_by_order(self):
        self.ramdisk_part_infos = sorted(self.ramdisk_part_infos, key=lambda part_info: part_info.order)

    def contains_lvm(self):
        return any(part_info.lvm_tree is not None for part_info in self.ramdisk_part_infos)
