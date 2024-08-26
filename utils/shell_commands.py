from __future__ import annotations

import json
import subprocess
import os
from typing import List


def check_output_wrapper(cmd: List[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def get_device_json_tree(device: str) -> dict:
    get_device_full_json_tree_cmd = ["lsblk", "--output-all", "--bytes", "--json", "--paths", "--inverse"]
    output = check_output_wrapper(get_device_full_json_tree_cmd + [device])

    j = json.loads(output)
    return j["blockdevices"][0]


def get_field_from_key_val(device: str, field: str, key: str, val: str) -> str | None:
    def check(_tree: dict, _field: str, _key: str, _val: str) -> str | None:
        if _key in _tree and _tree[_key] == _val:
            return _tree[_field]

        if "children" in _tree:
            return check(_tree["children"][0], _field, _key, _val)

        return None

    tree = get_device_json_tree(device)
    return check(tree, field, key, val)


def get_first_matching_field(device: str, field: str, continue_on_none: bool = True) -> str | None:
    def check(_tree: dict, _field: str, _continue_on_none: bool) -> str | None:
        if _field in tree:
            val = _tree[_field]

            if val is not None or not _continue_on_none:
                return val

        if "children" in _tree:
            return check(_tree["children"][0], _field, _continue_on_none)

        return None

    tree = get_device_json_tree(device)
    return check(tree, field, continue_on_none)


def get_mount_size(device: str) -> int:
    return int(get_first_matching_field(device, "size", False))


def get_disk_size(device: str) -> int:
    return int(get_field_from_key_val(device, "size", "type", "disk"))


def get_all_fields_from_key_val(device: str, field: str, key: str, val: str) -> List[str]:
    tree = get_device_json_tree(device)
    matches = set()

    def traverse(_tree: dict):
        if key in _tree and _tree[key] == val:
            matches.add(_tree[field])

        if "children" in _tree:
            for subtree in _tree["children"]:
                traverse(subtree)

    traverse(tree)
    return sorted(matches)


def get_device_disks(device: str) -> List[str]:
    return get_all_fields_from_key_val(device, "name", "type", "disk")


def get_device_partitions(device: str) -> List[str]:
    return get_all_fields_from_key_val(device, "name", "type", "part")


def get_device_type(device: str) -> str:
    device_tree = get_device_json_tree(device)
    return device_tree["type"]


def run_commands(*args: List[str]) -> None:
    for arg in args:
        # Early exit, if we don't have one of the commands, things will break anyway
        if not check_command(arg):
            return

        try:
            subprocess.run(arg)
        except FileNotFoundError:
            pass


def check_command(cmd: List[str]) -> bool:
    return os.path.exists(cmd[0])
