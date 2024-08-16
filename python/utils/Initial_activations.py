import subprocess


def activate_vgs() -> None:
    activate_cmd = ["/usr/sbin/vgchange", "-a", "y"]
    mknode_cmd = ["/usr/sbin/vgscan", "--mknodes"]

    try:
        subprocess.run(activate_cmd)
        subprocess.run(mknode_cmd)
    except FileNotFoundError:
        pass


def scan_btrfs() -> None:
    scan_cmd = ["/usr/sbin/btrfs", "device", "scan", "--all"]
    try:
        subprocess.run(scan_cmd)
    except FileNotFoundError:
        pass


def initial_activations():
    activate_vgs()
    scan_btrfs()