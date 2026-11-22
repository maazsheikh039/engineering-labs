# Linux Host Hardening, Kernel Auditing & Vulnerability Scanning

Practical Linux security engineering lab implementing least-privilege access control, `ufw`/`nftables` firewalling, X.509/GPG cryptography, Lynis and OpenSCAP compliance auditing, SSH hardening, `auditd` kernel monitoring, `fail2ban` intrusion prevention, and Trivy container/filesystem vulnerability scanning on Ubuntu.

## Objectives
- Enforce least-privilege user/group boundaries, restrictive file permissions, POSIX ACLs (`setfacl`/`getfacl`), and default login `umask` policies.
- Configure default-deny host firewall rules (`ufw`/`nftables`) with SSH rate-limiting and loopback-restricted application access.
- Generate and verify X.509 certificates with SANs (`OpenSSL`) and detached GPG signatures (`GnuPG`) with tamper detection.
- Run host baseline audits (`Lynis`, `OpenSCAP`), apply `sshd` hardening drop-ins, monitor syscalls/files with `auditd`, automate intrusion response with `fail2ban`, and scan container/filesystem targets with `Trivy`.

## Tools & Technologies Used
- **Access Control & Hardening:** `useradd`, `groupadd`, `chmod`, `umask`, `setfacl`, `getfacl`, `sshd` drop-ins
- **Network & Intrusion Prevention:** `ufw`, `nftables`, `nmap`, `ss`, `fail2ban` (`fail2ban-client`, `fail2ban-regex`)
- **Cryptography & Auditing:** `OpenSSL`, `GnuPG`, `auditd` (`auditctl`, `augenrules`, `ausearch`), `journalctl`, `Lynis`, `OpenSCAP` (`oscap`)
- **Containers & Vulnerability Management:** `Docker`, `Trivy`, `jq`, `Bash`

## Key Skills Demonstrated
- **Least Privilege & Need-to-Know:** Isolated service execution under a non-login system user (`appsvc`) and granted read-only inspection to `auditor` via POSIX ACLs without widening group access.
- **Defense in Depth & Attack Surface Reduction:** Combined `ufw`/`nftables` rate-limiting, loopback-only container port binding, and `sshd` hardening directives.
- **Forensic Telemetry & Automated Response:** Captured identity, privilege, and file access events in `auditd`, validated `fail2ban` regex matching and ban/unban actions, and built `watcher.sh` for threshold-based response.
- **Vulnerability & Compliance Management:** Generated Lynis, OpenSCAP, and Trivy JSON/table artifacts and mapped findings to package remediation details.

## Troubleshooting Log
- **OpenSCAP Profile Selection:** Extracting the Ubuntu 22.04 data stream (`ssg-ubuntu2204-ds.xml`) and querying `oscap info` ensured valid XCCDF profile evaluation and report generation.
- **`auditd` Rule Reloading:** Using `augenrules --load` after editing `/etc/audit/rules.d/acme.rules` synchronized persistent rule files with active kernel audit rules.
- **Loopback Service Isolation:** Binding the test container to `127.0.0.1:3000` and verifying with `ss -tlnp` confirmed local reachability without exposing the service on external interfaces.

## Quickstart
```bash
mkdir -p ~/u006-lab/{crypto,audit,reports,web}
cd ~/u006-lab

# Run automated validation checks
chmod +x ~/u006-lab/validate.sh
~/u006-lab/validate.sh

