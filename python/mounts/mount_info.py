from __future__ import annotations

import math
import os
from typing import List
from collections.abc import Sequence

from lvm.lvm_info import check_if_lvm, get_lvm_partition, get_lvm_size, get_lvm_map
from raid.raid_info import check_if_raid
from utils.shell_commands import check_output_wrapper


class MountInfo:
    """
        Represents information about a mount point from an fstab entry.
    """
    # Need to create a more comprehensive list
    REMOTE_FSTYPES = {"nfs", "nfs4", "cifs", "fuse.s3fs", "fuse.ceph"}
    SOFT_FSTYPES = {"swap", "tmpfs", "ramfs"}

    READLINK_CMD = ["readlink", "--canonicalize"]
    SIZE_CMD = ["lsblk", "--nodeps", "--noheadings", "--bytes", "--output", "SIZE"]

    def __init__(self, source: str, dest: str, fstype: str, fsopts: List[str], dump: str, fsck: str):
        """Initialize a MountInfo object with information from an fstab entry.

        Args:
            source (str): The source device or filesystem.
            dest (str): The mount point destination.
            fstype (str): The filesystem type.
            fsopts (List[str]): List of mount options.
            dump (str): Dump field from fstab.
            fsck (str): Fsck field from fstab.
        """

        # Base values from fstab
        self.source: str = source
        self.dest: str = dest
        self.fstype: str = fstype
        self.fsopts: List[str] = fsopts
        self.dump: str = dump
        self.fsck: str = fsck
        self._initialized: bool = False

        # Derived values
        self._is_lvm: bool | None = None
        self._is_raid: bool | None = None
        self._uuid: str | None = None
        self._part_uuid: str | None = None
        self._label: str | None = None
        self._partition: str | None = None
        self._size_gb: int | None = None
        self._parent_disk: str | None = None
        self._parent_size_gb: int | None = None

    def initialize(self):
        if self._initialized:
            return

        # Figure out some values
        self._uuid = self.get_uuid()
        self._label = self.get_label()
        self._part_uuid = self.get_part_uuid()

        # Checking if source can be better mapped to a device
        self.source = self.update_source()

        # Figure out if we're on an lvm
        self._is_lvm = self.is_lvm()
        self._is_raid = self.is_raid()

        # Check source again if we're on an lvm
        self.source = self.update_lvm_source()

        # Continue figuring out values
        self._partition = self.get_partition()
        self._size_gb = self.get_size_gb()
        self._parent_disk = self.get_parent_disk()
        self._parent_size_gb = self.get_parent_size_gb()

        # Setting initialized flag
        self._initialized = True

    def __eq__(self, other: MountInfo) -> bool:
        """Determine if two MountInfo objects represent the same mount.

        Args:
            other (MountInfo): Another MountInfo to compare equality to.

        Returns:
            bool: True if the MountInfo objects represent the same mount, False otherwise.
        """
        if self.dest == other.dest:
            return True

        return False

    @classmethod
    def create_mount_info(cls, fstab_line: str) -> MountInfo:
        """Create a MountInfo object from a line in an fstab file.

        Args:
            fstab_line (str): A single line from an fstab file.

        Returns:
            MountInfo: A MountInfo object.
        """
        source, dest, fstype, fsargs, dump, fsck = fstab_line.split()

        return MountInfo(source, dest, fstype, fsargs.split(","), dump, fsck)

    # Boolean checks for type
    def is_remote(self) -> bool:
        """Check if the mount is a remote filesystem.

        Returns:
            bool: True if the filesystem is remote, False otherwise.
        """
        return self.fstype in MountInfo.REMOTE_FSTYPES

    def is_root(self) -> bool:
        """Check if this is the root mount.

        Returns:
            bool: True if this is the root mount, False otherwise.
        """
        return self.dest == "/"

    def is_physical(self) -> bool:
        """Check if this is a physical mount.

        Returns:
            bool: True if this is a physical mount, False otherwise.
        """
        return self.fstype not in MountInfo.SOFT_FSTYPES | MountInfo.REMOTE_FSTYPES or self.is_root()

    def is_lvm(self) -> bool:
        """Check if this is an LVM mount.

        Returns:
            bool: True if this is an LVM mount, False otherwise.
        """
        if self._is_lvm is not None:
            return self._is_lvm

        if not self.is_physical() or self.is_remote():
            return False

        return check_if_lvm(self.source)

    def is_raid(self):
        """Check if this is a RAID mount.

        Returns:
            bool: True if this is a RAID mount, False otherwise.
        """
        if self._is_raid:
            return self._is_raid

        if not self.is_physical() or self.is_remote():
            return False

        return check_if_raid(self.source)

    def get_uuid(self) -> str | None:
        """Get the UUID of the mount.

        Returns:
            str | None: The UUID if available, None otherwise.
        """
        if self._uuid is not None:
            return self._uuid

        if self.source.startswith("/dev/disk/by-uuid/"):
            return os.path.basename(self.source)

        if self.source.upper().startswith("UUID="):
            return self.source.split("=")[-1]

    def get_label(self) -> str | None:
        """Get the label of the mount.

        Returns:
            str | None: The label if available, None otherwise.
        """
        if self._label is not None:
            return self._label

        if self.source.startswith("/dev/disk/by-label"):
            return os.path.basename(self.source)

        if self.source.upper().startswith("LABEL="):
            return self.source.split("=")[-1]

    def get_part_uuid(self) -> str | None:
        """Get the partition UUID of the mount.

        Returns:
            str | None: The partition UUID if available, None otherwise.
        """
        if self._part_uuid is not None:
            return self._part_uuid

        if self.source.startswith("/dev/disk/by-partuuid/"):
            return os.path.basename(self.source)

        if self.source.upper().startswith("PARTUUID="):
            return self.source.split("=")[-1]

    def update_source(self) -> str:
        """Update the source to a better device mapping if possible.

        Returns:
            str: The updated source path.
        """
        if self.get_uuid() is not None:
            return os.path.join("/dev/disk/by-uuid", self.get_uuid())

        if self.get_part_uuid() is not None:
            return os.path.join("/dev/disk/by-partuuid", self.get_part_uuid())

        if self.get_label() is not None:
            return os.path.join("/dev/disk/by-label", self.get_label())

        return self.source

    def update_lvm_source(self):
        """Update the source to a better device mapping if we are an lvm.

        Returns:
            str: The updated source path.
        """
        if self.is_lvm() and os.path.exists(self.source):
            # If we're an lvm, get the mapper name as it's immensely more useful
            return get_lvm_map(self.source)

        return self.source

    def get_partition(self) -> str | None:
        """Get the partition information for this mount.

        Returns:
            str | None: The partition path if available, None otherwise.
        """
        if self._partition is not None:
            return self._partition

        if self.is_lvm():
            return get_lvm_partition(self.source)

        if self.is_raid():
            return self.source

        if not self.is_physical() or self.is_remote():
            return None

        # If any of these aren't None, we should have a good place to check for the partition
        if any(val is not None for val in (self._uuid, self._part_uuid, self._label)):
            return check_output_wrapper(MountInfo.READLINK_CMD + [self.source])

        if self.source.startswith("/dev"):
            return self.source

    def get_parent_disk(self) -> str | None:
        """Get the parent disk of this mount's partition.

        Returns:
            str | None: The parent disk path if available, None otherwise.
        """
        if self._parent_disk is not None:
            return self._parent_disk

        if self.is_raid():
            return self.source

        if self._partition is not None:
            partition_base = os.path.basename(self._partition)

            # Symlink points to the parent of the partition
            parent_full = check_output_wrapper(MountInfo.READLINK_CMD + [f"/sys/class/block/{partition_base}/.."])

            return f"/dev/{os.path.basename(parent_full)}"

    def get_parent_size_gb(self) -> int | None:
        """Get the size of the parent disk in gigabytes.

        Returns:
            int | None: The size in GB if available, None otherwise.
        """
        if self._parent_size_gb is not None:
            return self._parent_size_gb

        if self.is_raid():
            return self.get_size_gb()

        if self._parent_disk is not None:
            size_in_bytes = check_output_wrapper(MountInfo.SIZE_CMD + [self._parent_disk])

            # Convert from bytes to GB
            return math.ceil(float(size_in_bytes) / 1024 ** 3)

    def get_size_gb(self) -> int | None:
        """Get the size of this mount's partition in gigabytes.

        Returns:
            int | None: The size in GB if available, None otherwise.
        """
        if self._size_gb is not None:
            return self._size_gb

        if self.is_lvm():
            return get_lvm_size(self.source)

        if self._partition is not None:
            size_in_bytes = check_output_wrapper(MountInfo.SIZE_CMD + [self._partition])

            # Convert from bytes to GB
            return math.ceil(float(size_in_bytes) / 1024 ** 3)

    def get_dest_depth(self) -> int | float:
        """Calculate the depth of the mount point in the filesystem hierarchy.

        Returns:
            int | float: The depth as an integer, or float('inf') for odd cases.
        """
        # i.e. '/'
        if self.dest == os.path.sep:
            return 1

        # Strip trailing / to not count it
        count = self.dest.rstrip(os.path.sep).count(os.path.sep)

        # If there isn't a /, it's something odd
        if count == 0:
            return float("inf")

        # 1 == root, 2 == /var, 3 == /var/log, etc.
        return count + 1

    def to_fstab_line(self) -> str:
        """Convert this MountInfo object back to an fstab line format.

        Returns:
            str: A string representing this mount in fstab format.
        """
        return f"{self.source}\t{self.dest}\t{self.fstype}\t{','.join(self.fsopts)}\t{self.dump}\t{self.fsck}"


class AllMounts(Sequence):
    """Represents a collection of MountInfo objects, typically all mounts in a system."""

    def __init__(self, mount_list: List[MountInfo]):
        """Initialize an AllMounts object with a list of MountInfo objects.

        Args:
            mount_list (List[MountInfo]): A list of MountInfo objects.
        """

        # Initialize List
        self.mount_list = []

        # Make sure root gets in
        self.mount_list.append(next(mount for mount in mount_list if mount.is_root()))

        # Remove duplicates on creation using equality check
        for mount in mount_list:
            if mount not in self.mount_list:
                self.mount_list.append(mount)

        for mount in self.mount_list:
            mount.initialize()

        # Sort by depth on creation
        self._sort_by_depth()

    def __next__(self) -> MountInfo:
        """Implement the iterator protocol for AllMounts.

        Returns:
            MountInfo: The next MountInfo object in the sequence.
        """
        for mount in self.mount_list:
            yield mount

    def __len__(self) -> int:
        """Get the number of mounts in this collection.

        Returns:
            int: The number of mounts.
        """
        return len(self.mount_list)

    def __getitem__(self, item) -> MountInfo:
        """Get a specific MountInfo object by index.

        Args:
            item: The index of the desired MountInfo object.

        Returns:
            MountInfo: The MountInfo object at the specified index.
        """
        return self.mount_list[item]

    def _sort_by_depth(self) -> None:
        """Sort the mount list by the depth of their mount points."""
        self.mount_list = sorted(self.mount_list, key=lambda mount: mount.get_dest_depth())

    def get_physical_mounts(self) -> AllMounts:
        """Get a new AllMounts object containing only physical mounts.

        Returns:
            AllMounts: An AllMounts object with only physical mounts.
        """
        return AllMounts([mount for mount in self.mount_list if mount.is_physical()])

    def get_root_mount(self) -> MountInfo:
        """Get the root mount from this collection.

        Returns:
            MountInfo: The MountInfo object representing the root mount.
        """
        return next(mount for mount in self.mount_list if mount.dest == "/")
