# Production Linux Hardening, LVM Storage, Systemd & Incident Response

Hardens a Linux host for an internal Python reporting API (`ReportApp`), covering identity and least-privilege `sudo` delegation, collaborative directory permissions with setgid/sticky bits and POSIX ACLs, LVM volume expansion and persistent `fstab` mounts, sandboxed `systemd` units, SSH/UFW firewalling with network namespaces, log analysis and `copytruncate` rotation, automated retention backups, and live CPU/I/O/storage incident response.

## Objectives

- Provision role-scoped groups, password ageing/expiry policies, and validated `sudoers.d` rules without interactive root pager escapes.
- Enforce collaborative directory sharing (`setgid`, sticky bit, default and access ACLs) and audit special permission bits across the filesystem.
- Build and online-expand LVM storage across loop-backed devices with `ext4` and `XFS` filesystems, UUID mounts, and boot-time loop attachment.
- Run a Python HTTP service under a restricted system account with `systemd` sandboxing (`ProtectSystem=strict`, `ReadWritePaths=`), resource limits (`MemoryMax`, `CPUQuota`, `TasksMax`), and `strace` syscall diagnostics.
- Harden `sshd` via drop-ins, configure default-deny `ufw` (`nftables`) rules, and validate LAN-only service reachability using a network namespace.
- Parse access logs with `awk`, `sed`, `sort`, `uniq`, and `numfmt`, package a `set -euo pipefail` reporting CLI, and resolve open-file descriptor loss during `logrotate` runs using `copytruncate`.
- Automate retention-pruned, checksummed backups via `systemd` timers (including LVM snapshot backups with `ro,noload` and `OnFailure` alerting) alongside `cron` reporting jobs.
- Triage and remediate a user-space CPU spin incident (`uptime`, `vmstat`, `pidstat`, `renice`, `SIGTERM`) and a deleted-but-open file space leak (`lsof +L1`, `/proc/<PID>/fd`).

## Tools Used

- **OS & System Management:** Ubuntu Linux, `systemd` (`systemctl`, `journalctl`, `systemd-analyze`, `systemd-run`), `cron`, `logrotate`, `sysstat` (`sar`, `pidstat`, `iostat`)
- **Identity & Access:** `groupadd`, `useradd`, `usermod`, `chage`, `passwd`, `visudo`, `setfacl`, `getfacl`, `find`
- **Storage & Filesystems:** `losetup`, `truncate`, `parted`, `fdisk`, `lsblk`, `pvcreate`, `vgcreate`, `vgextend`, `lvcreate`, `lvextend`, `mkfs.ext4`, `mkfs.xfs`, `blkid`, `findmnt`, `mountpoint`, `rsync`, `tar`, `sha256sum`
- **Networking & Security:** `ip`, `ss`, `nc`, `curl`, `sshd`, `ufw`, `nft`
- **Diagnostics & Scripting:** `bash`, `python3`, `strace`, `lsof`, `ps`, `top`, `vmstat`, `renice`, `kill`, `pkill`, `awk`, `sed`, `grep`, `numfmt`

## Key Skills Demonstrated

- Least-privilege RBAC/sudoers validation (`visudo -cf`) and POSIX ACL mask/inheritance design.
- Zero-downtime storage growth (`vgextend`, `lvextend -r`) and safe `/etc/fstab` UUID mount engineering (`nofail`, `x-systemd.device-timeout`).
- Service hardening, drop-in overrides, syscall-level troubleshooting (`strace -e trace=openat`), and network namespace isolation testing.
- Safe shell scripting (`set -euo pipefail`, avoiding `SIGPIPE` at pipeline ends) and daemon log-rotation correctness (`lsof` inode verification + `copytruncate`).
- Evidence-driven production incident triage across CPU contention, block I/O saturation, and unlinked open file descriptors.

## Troubleshooting Log

- **Password ageing & user group flags:** Enforced `chage -M 90 -m 1 -W 14` with proper flag prefixes and used `usermod -aG` to append supplementary groups rather than overwriting existing group memberships.
- **Sudoers syntax & alias formatting:** Fixed broken line continuations and alias naming in `devops.sudoers` and verified syntax with `visudo -cf` prior to installing at mode `0440`.
- **ACL & `find` flag formatting:** Fixed colon-delimited ACL specs (`g:auditors:rx`), default ACL flags (`setfacl -d -m`), `setfacl --restore` syntax, and `find` predicate spacing/negation flags.
- **LVM & `fstab` mount options:** Corrected `lvcreate` argument placement, removed spaces from comma-separated `fstab` mount options (`defaults,nofail,nodev,nosuid,x-systemd.device-timeout=10s`), fixed `fallocate -l` and `df -h` spacing, and closed the heredoc delimiter in `lab-loopdisks.service`.
- **Service startup & Python API bugs:** Fixed `install -d -o` and CSV/tee redirections, repaired Python config parsing (`key, _, value = line.partition("=")`), `buffering=1`, `_reply`, `end_headers()`, `LOG_FH`, and `if __name__ == "__main__":`, corrected `systemd` unit `=` assignments and `systemctl enable --now`, and fixed `report-summary` list brackets, assignment syntax, and `strace` inspection.
- **SSH, `ufw` & namespace commands:** Fixed `AllowAgentForwarding`, `ssh-keygen` flags (`-t ed25519 -N "" -f ...`), `ssh -i`, `nc -zv -w 3`, `ufw` rule formatting, and `sshd -T` filter expressions.
- **Log generation, text pipelines & `logrotate`:** Repaired `gen_access_log.py` list/tuple delimiters, loop index `i`, and `print` formatting; fixed `awk`/`sed`/`cmp` expressions; used `ls -1t` in backup retention pruning so full `ls -l` columns never break `rm -f`; fixed `systemd` timer `OnCalendar` and `cron` spacing/`crontab -l` flags; and replaced `create` with `copytruncate` after confirming `lsof` showed `reportapp` writing to `access.log.1`.
- **Incident scripts, `validate.sh` & snapshot backup:** Fixed the `report-indexer` infinite loop syntax (`while true; do ... done`), `ps`/`pidstat`/`systemd-run`/`du` flags, `kill -l` flag (`-l`, not `-1`), `validate.sh` comparisons/quoting, and snapshot backup mount options (`-o ro,noload`) and `OnFailure` unit wiring.
