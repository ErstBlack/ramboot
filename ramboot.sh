#!/bin/bash

export PATH=$PATH:/usr/sbin:/usr/local/bin:/usr/bin:/bin

mount --options remount,rw /

/root/ramboot

exec chroot . init
