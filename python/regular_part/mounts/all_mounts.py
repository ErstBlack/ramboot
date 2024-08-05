from __future__ import annotations

from collections.abc import Sequence
from typing import List

from regular_part.mounts.mount_info import MountInfo


class AllMounts(Sequence):
    def __init__(self, mount_list: List[MountInfo]):
        self.mount_list: List[MountInfo] = mount_list

    def __next__(self) -> MountInfo:
        for mount in self.mount_list:
            yield mount

    def __len__(self) -> int:
        return len(self.mount_list)

    def __getitem__(self, item) -> MountInfo:
        return self.mount_list[item]

    def get_physical_mounts(self) -> AllMounts:
        return AllMounts([mount for mount in self.mount_list if mount.is_physical()])

    def get_soft_mounts(self) -> AllMounts:
        return AllMounts([mount for mount in self.mount_list if not mount.is_physical()])

    def sort_by_depth(self) -> None:
        self.mount_list = sorted(self.mount_list, key=lambda mount: mount.get_dest_depth())

    def get_root_mount(self) -> MountInfo:
        return next(mount for mount in self.mount_list if mount.dest == "/")
