from utils.shell_commands import get_device_type


def check_if_raid(device: str) -> bool:
    raid_prefix = "raid"
    block_type = get_device_type(device)

    return block_type.startswith(raid_prefix)
