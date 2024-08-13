import math
import subprocess

CHECK_LVM_CMD = ["lsblk", "--output", "TYPE", "--noheadings"]
GET_VG_CMD = ["/sbin/lvs", "--noheadings", "--options", "vg_name"]
GET_PV_CMD = ["/sbin/vgs", "--noheadings", "--options", "pv_name"]
GET_LV_SIZE_CMD = ["/sbin/lvs", "--noheadings", "--options", "lv_size", "--units", "g", "--nosuffix"]

LVM_TYPES = {"lvm", "lvm2"}

def check_if_lvm(device: str) -> bool:
    output = subprocess.check_output(CHECK_LVM_CMD + [device]).decode("utf-8").strip().lower()

    return output in LVM_TYPES


def get_lvm_vg(device: str) -> str:
    return subprocess.check_output(GET_VG_CMD + [device]).decode("utf-8").strip()


def get_lvm_partition(device: str) -> str:
    vg = get_lvm_vg(device)

    return subprocess.check_output(GET_PV_CMD + [vg]).decode("utf-8").strip()


def get_lvm_size(device: str) -> int:
    return math.ceil(float(subprocess.check_output(GET_LV_SIZE_CMD + [device]).decode("utf-8").strip()))


def activate_vgs():
    activate_cmd = ["/sbin/vgchange", "-a", "y"]
    mknode_cmd = ["/sbin/vgscan", "--mknodes"]

    subprocess.run(activate_cmd)
    subprocess.run(mknode_cmd)

def deactivate_vgs():
    # TODO: Best option might be to loop over /sbin/dmsetup ls, clean up lvms, then check vg and pv?
    pass