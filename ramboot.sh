#!/bin/bash

export PATH=$PATH:/usr/sbin:/usr/local/bin:/usr/bin:/bin

mount --options remount,rw /

/usr/sbin/ramboot/ramboot

exec chroot . init
