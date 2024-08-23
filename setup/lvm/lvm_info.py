from utils.shell_commands import check_output_wrapper, get_device_type, get_field_from_key_val


def check_if_lvm(device: str) -> bool:
    lvm_types = {"lvm", "lvm2"}
    block_type = get_device_type(device)

    return block_type in lvm_types


def get_lvm_vg(device: str) -> str:
    get_vg_cmd = ["/usr/sbin/lvs", "--noheadings", "--options", "vg_name"]

    return check_output_wrapper(get_vg_cmd + [device])


def get_lvm_map(device: str) -> str:
    return get_field_from_key_val(device, "name", "type", "lvm")
