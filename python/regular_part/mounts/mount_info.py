from __future__ import annotations

import os.path
from math import ceil
from os.path import basename
from subprocess import check_output
from typing import List


class MountInfo:
    REMOTE_FSTYPES = {"nfs", "nfs4", "cifs"}
    SOFT_FSTYPES = {"swap", "tmpfs", "ramfs"}
    READLINK_CMD = ["readlink", "--canonicalize"]
    LSBLK_CMD = ["lsblk", "--nodeps", "--noheadings", "--bytes", "--output", "SIZE"]

    def __init__(self, source: str, dest: str, fstype: str, fsopts: List[str], dump: str, fsck: str):
        # Base values from fstab
        self.source = source
        self.dest = dest
        self.fstype = fstype
        self.fsopts = fsopts
        self.dump = dump
        self.fsck = fsck

        # Derived values
        self.uuid = self.get_uuid()
        self.partition = None
        self.label = None
        self.parent_disk = None
        self.parent_size_gb = None

        # Figure out some values
        self.partition = self.get_partition()
        self.parent_disk = self.get_parent_disk()
        self.parent_size_gb = self.get_parent_size_gb()

    @classmethod
    def create_mount_info(cls, fstab_line: str) -> MountInfo:
        source, dest, fstype, fsargs, dump, fsck = fstab_line.split()

        return MountInfo(source, dest, fstype, fsargs.split(","), dump, fsck)

    def is_remote(self) -> bool:
        return self.fstype in MountInfo.REMOTE_FSTYPES

    def is_root(self) -> bool:
        return self.dest == "/"

    def get_uuid(self) -> str | None:
        if self.source.startswith("/dev/disk/by-uuid/"):
            return basename(self.source)

        if self.source.upper().startswith("UUID="):
            return self.source.split("=")[-1]

    def get_label(self) -> str | None:
        if self.source.startswith("/dev/disk/by-label"):
            return basename(self.source)

        if self.source.upper().startswith("LABEL="):
            return self.source.split("=")[-1]

    def get_partition(self) -> str | None:
        if self.partition is not None:
            return self.partition

        if self.uuid is not None:
            partition = check_output(
                MountInfo.READLINK_CMD + [f"/dev/disk/by-uuid/{self.uuid}"]).decode("utf-8").strip()
            return partition

        if self.label is not None:
            partition = check_output(
                MountInfo.READLINK_CMD + [f"/dev/disk/by-label/{self.uuid}"]).decode("utf-8").strip()
            return partition

        if self.source.startswith("/dev"):
            return self.source

    def get_parent_disk(self) -> str | None:
        if self.parent_disk is not None:
            return self.parent_disk

        if self.partition is not None:
            partition_base = basename(self.partition)
            parent_full = check_output(
                MountInfo.READLINK_CMD + [f"/sys/class/block/{partition_base}/.."]).decode("utf-8").strip()

            return f"/dev/{basename(parent_full)}"

    def get_dest_depth(self) -> int | float:
        if self.dest == os.path.sep:
            return 1

        count = self.dest.rstrip(os.path.sep).count(os.path.sep)
        if count == 0:
            return float("inf")

        return count + 1

    def get_parent_size_gb(self) -> int | None:
        if self.parent_size_gb is not None:
            return self.parent_size_gb

        if self.parent_disk is not None:
            size_in_bytes = check_output(MountInfo.LSBLK_CMD + [self.parent_disk]).decode("utf-8").strip()
            return ceil(int(size_in_bytes) / 1024 ** 3)

    def is_physical(self) -> bool:
        return self.partition is not None and self.fstype not in MountInfo.SOFT_FSTYPES

    def to_fstab_line(self) -> str:
        return f"{self.source}\t{self.dest}\t{self.fstype}\t{self.fsopts}\t{self.dump}\t{self.fsck}"
