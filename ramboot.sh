#!/bin/bash

mount --options remount,rw /

/root/ramboot

exec /sbin/chroot . /sbin/init
