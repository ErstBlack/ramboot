#!/bin/bash

set -x

# Check if required lvs commands exist
if command -v /sbin/lvs &>/dev/null; then

	# Check if LVM exists
	LVM_COUNT=$(/sbin/lvs --noheadings | awk '{print $2}' | sort --unique | wc -l)
	
	# If so, map them
	if [ "${LVM_COUNT}" -gt 0 ]; then
		# Activate all of the vgs
		for vg in $(/sbin/lvs --noheadings | awk '{print $2}' | sort --unique ); do
			/sbin/vgchange -a y "${vg}"
		done
	
		# Create mapper entries
		/sbin/vgscan --mknodes	
	fi

fi

# Remount / to make writeable
mount --options remount,rw /
mount --all --types xfs

# Create ramdisk mountpoint
RAMDISK=/mnt/ramdisk-ramboot
rmdir "${RAMDISK}" 
mkdir "${RAMDISK}"

# Create ramdisk
MAX_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2 }')
/sbin/modprobe brd rd_nr=1 rd_size=$(( MAX_MEM - ( MAX_MEM / 10 ) ))

# Format and mount the ramdisk
/sbin/mkfs.xfs /dev/ram0
mount /dev/ram0 "${RAMDISK}"

# Copy old file system onto the ramdisk
for point in $(findmnt --real --list --output=TARGET --noheadingsu | grep -v "${RAMDISK}"); do
	cp --archive --one-file-system "${point}" "${RAMDISK}$(basename ${point})"
done

# Clearing /etc/fstab
> "${RAMDISK}"/etc/fstab

# Move important mountpoints on the new file system
for point in dev proc sys run; do
	mount --move /"$point" "${RAMDISK}"/"$point"
done

# Create a pivot_root point
mkdir "${RAMDISK}"/oldroot

# Pivot to the new root
cd "${RAMDISK}"
./sbin/pivot_root . oldroot

# Unmount all xfs mounts
#umount --lazy --all --types xfs
umount --all-targets --lazy --recursive /oldroot

# Continue boot
exec /sbin/chroot . /sbin/init
