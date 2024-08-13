from boot import part_boot
from lvm.lvm_info import activate_vgs


def main():
    activate_vgs()
    part_boot()


if __name__ == "__main__":
    main()
