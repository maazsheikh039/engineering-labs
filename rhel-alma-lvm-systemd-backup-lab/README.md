# Multi-Host Linux SysOps, LVM Storage, Firewalld & Automated Backup Lab

## Objectives
- Provision and manage LVM physical volumes, volume groups, logical volumes, XFS filesystems, and UUID-backed swap across GPT (`parted`) and MBR (`fdisk`) loop devices with safe `fstab` mount options.
- Build and run `systemd`-enabled Rocky Linux 9 (`app01`) and AlmaLinux 9 (`bkp01`) containers on a custom bridge network (`rhelnet`) with shared host kernel modules.
- Manage RPM packages and detect/repair configuration and permission drift using `rpm` and `dnf`, including publishing a GPG-verified local repository.
- Enforce least-privilege access using Linux users/groups, password aging (`chage`, `/etc/login.defs`), setgid directories, POSIX default/access ACLs, and `sudoers.d` command aliases.
- Configure `httpd` on a custom port with `systemd` drop-in crash recovery (`Restart=on-failure`), persistent `journald` storage, and an SELinux enforcement runbook (`semanage`, `restorecon`).
- Lock down host traffic with `firewalld` zones, custom services, and rich rules alongside `NetworkManager` (`nmcli`) zone bindings.
- Harden OpenSSH (`sshd_config.d`), automate `rsync` + `.tar.gz` backups via `systemd` timers and `cron`, perform a restore drill, and execute live LVM/swap extensions and `pvmove` disk migration.

## Tools Used
- **OS & Virtualization:** Ubuntu Linux (host), Rocky Linux 9 (`app01`), AlmaLinux 9 (`bkp01`), Docker Engine, `systemd`, `journalctl`
- **Storage & Filesystems:** `parted`, `fdisk`, `losetup`, `lvm2` (`pvcreate`, `vgcreate`, `vgextend`, `vgreduce`, `lvcreate`, `lvextend`, `pvmove`), `mkfs.xfs`, `mkswap`, `swapon`, `/etc/fstab`
- **Package & Repo Management:** `rpm`, `dnf`, `createrepo_c`
- **Access Control & Security:** `useradd`, `usermod`, `chage`, `passwd`, `setfacl`, `getfacl`, `visudo`, `semanage`, `restorecon`, `firewalld` (`firewall-cmd`), `nmcli`, OpenSSH (`sshd`)
- **Automation & Verification:** `rsync`, `tar`, `cron` (`/etc/cron.d`, `crontab`), Bash scripting

## Key Skills Demonstrated
- **Infrastructure & Storage Engineering:** Designing persistent LVM/XFS/swap layouts, executing zero-downtime capacity expansions, preserving swap UUIDs across resize operations, and migrating live extents off a disk via `pvmove`.
- **Linux Systems Administration:** Running `systemd` inside containers, authoring drop-in unit overrides, diagnosing service failures via status/logs/config checks, and writing SELinux policy runbooks for non-standard ports and paths.
- **Security & Network Hardening:** Implementing least-privilege `sudo` policies, setgid + ACL team permissions, `firewalld` zone/rich-rule filtering, `NetworkManager` interface/zone control, and key-only SSH hardening.
- **Backup & Reliability Operations:** Building repeatable `rsync` + archive pipelines scheduled via `systemd` timers and `cron`, validating restores, and verifying system state with an automated check script.

## Troubleshooting Log
- **Malformed/broken lab commands & flags:** Fixed missing option dashes/spaces across `truncate -s`, `parted`, `fdisk -l`, `blkid -s UUID`, `docker run`/`exec` flags, `rpm --import`, `createrepo_c`, `dnf` flags, `chage`, `setfacl`, `curl` retry flags, `ss -tlnp`, `nmcli -f` field lists, `fallocate -l`, `lvextend -r -L`, `lvreduce`, `swapon --show`, `pvs`/`lvs` flags, and `validate.sh` helper functions.
- **Broken container `Dockerfile` & unit syntax:** Fixed unexpanded `BASE_IMAGE` handling inside the `Dockerfile` heredoc, corrected `docker build --build-arg` syntax, and repaired systemd directive formatting (`Storage=persistent`, `SystemMaxUse=100M`, `RestartSec=5s`, `OnCalendar=*:0/15`, `Wants=`, `After=`, `Type=`).
- **Template placeholders & text encoding artifacts:** Replaced starter `TODO` blocks in `localrepo.repo`, `/etc/sudoers.d/webdev`, `pull-app01-backup.sh`, `app01-backup.timer`, and `/root/selinux-httpd-runbook.sh`, and normalized corrupted characters/expressions from PDF extraction.
- **Simulated operational incidents:** Resolved a broken `httpd` `DocumentRoot` directive, verified automatic recovery after `SIGKILL` via a `systemd` drop-in override, handled an `lvextend` out-of-space error by extending `vg_lab` with an additional PV, and confirmed XFS does not support shrinking while preserving swap UUIDs across resize.
