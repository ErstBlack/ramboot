import math
import os.path
import subprocess
from typing import List


def check_output_wrapper(cmd: List[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def check_if_lvm(device: str) -> bool:
    check_lvm_cmd = ["lsblk", "--output", "TYPE", "--noheadings"]
    lvm_types = {"lvm", "lvm2"}

    output = check_output_wrapper(check_lvm_cmd + [device]).lower()

    return output in lvm_types


def get_lvm_vg(device: str) -> str:
    get_vg_cmd = ["/usr/sbin/lvs", "--noheadings", "--options", "vg_name"]

    return check_output_wrapper(get_vg_cmd + [device])


def get_lvm_partition(device: str) -> str:
    get_pv_cmd = ["/usr/sbin/vgs", "--noheadings", "--options", "pv_name"]

    vg = get_lvm_vg(device)
    return check_output_wrapper(get_pv_cmd + [vg])


def get_lvm_size(device: str) -> int:
    get_lv_size_cmd = ["/usr/sbin/lvs", "--noheadings", "--options", "lv_size", "--units", "g", "--nosuffix"]

    return math.ceil(float(check_output_wrapper(get_lv_size_cmd + [device])))


def get_lvm_map(device: str) -> str:
    # Quick exit if we're already here
    if os.path.dirname(device) == "/dev/mapper":
        return device

    readlink_cmd = ["readlink", "--canonicalize"]
    name_prefix = "/sys/class/block"
    name_suffix = "dm/name"

    dm_name = check_output_wrapper(readlink_cmd + [device])
    name_path = os.path.join(name_prefix, os.path.basename(dm_name), name_suffix)

    if os.path.exists(name_path):
        with open(name_path, "r") as f:
            name = f.readline().strip()
            return os.path.join("/dev/mapper", name)
