ARG BASE_IMAGE=rockylinux/rockylinux:9
FROM ${BASE_IMAGE}
ENV container=docker

RUN dnf -y install systemd dbus sudo passwd shadow-utils acl procps-ng \
  iproute iputils findutils which less vim-minimal hostname \
  dnf-plugins-core util-linux diffutils file \
  && (command -v curl >/dev/null || dnf -y install curl-minimal) \
  && dnf clean all

RUN systemctl mask \
  systemd-udevd.service systemd-udevd-control.socket systemd-udevd-kernel.socket \
  systemd-udev-trigger.service systemd-udev-settle.service \
  systemd-sysctl.service systemd-modules-load.service \
  systemd-binfmt.service proc-sys-fs-binfmt_misc.automount proc-sys-fs-binfmt_misc.mount \
  systemd-remount-fs.service dev-hugepages.mount sys-fs-fuse-connections.mount \
  sys-kernel-config.mount sys-kernel-debug.mount sys-kernel-tracing.mount \
  getty.target console-getty.service systemd-firstboot.service

STOPSIGNAL SIGRTMIN+3
CMD ["/usr/sbin/init"]
