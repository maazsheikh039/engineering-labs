# Linux Host Security Hardening, Auditing & Vulnerability Testing

Hands-on security engineering lab implementing access controls, cryptography, host audit logging, firewall enforcement, compliance auditing, container vulnerability scanning, and dynamic web application testing on Ubuntu Linux.

## Objectives
- Enforce least-privilege access control via `sudoers` drop-ins, POSIX ACLs (`setfacl`/`getfacl`), PAM password complexity (`pam_pwquality`), and account lockout policies (`pam_faillock`).
- Apply symmetric encryption (`AES-256-CBC` with PBKDF2), internal Root CA + X.509 certificate issuance with SANs (`OpenSSL`), and detached digital signatures (`GnuPG`) with tamper detection.
- Configure host audit logging (`auditd`, `ausearch`, `aureport`) and default-deny host firewalling (`ufw` / `nftables`), verified against external interface scans (`nmap`).
- Run host security benchmarks (`Lynis`, `OpenSCAP`), container image CVE scans (`Trivy`), and headless dynamic web security scans (`OWASP ZAP`) against a containerized target with automated validation.

## Tools & Technologies Used
- **IAM & Host Access Controls:** `sudo`, `visudo`, POSIX ACLs (`setfacl`, `getfacl`), PAM (`pam_pwquality`, `pam_faillock`)
- **Cryptography & PKI:** `OpenSSL` (`genrsa`, `req`, `x509`, `enc`), `GnuPG` (`gpg`), `Nginx` TLS reverse proxy
- **Telemetry & Firewalling:** `auditd`, `augenrules`, `ausearch`, `aureport`, `ufw`, `nftables`, `nmap`
- **Compliance & Security Testing:** `Lynis`, `OpenSCAP` (`oscap`), `Docker`, `Trivy`, `OWASP ZAP`, `jq`, `Bash`

## Key Skills Demonstrated
- **Least-Privilege & Identity Hardening:** Scoped `sudo` privileges to explicit service operations, restricted log access via POSIX ACLs without weakening base ownership, and enforced password complexity and lockout thresholds.
- **Applied Cryptography & PKI Operations:** Encrypted sensitive configuration files at rest, issued SAN-enabled X.509 certificates from a private Root CA, and validated integrity/non-repudiation with GnuPG detached signatures.
- **Detective & Preventive Operations:** Monitored identity, privilege, and application log paths in `auditd` and enforced a default-deny inbound firewall (`ufw`/`nftables`) with port-scan verification.
- **Automated Security Assessment:** Generated Lynis and OpenSCAP compliance artifacts, scanned container images for CVEs with Trivy, executed headless OWASP ZAP baseline scans, and verified posture via `validate.sh`.

## Troubleshooting Log
- **Loopback vs. External Firewall Testing (`nmap`):** Scanning `127.0.0.1` showed non-allowed ports as open because loopback traffic is not blocked by default `ufw` rules; scanning the host's primary interface IP confirmed default-deny filtering on unapproved ports.
- **Root `chpasswd` Bypassing `pwquality`:** Password updates performed as `root` via `chpasswd` bypass PAM quality checks; testing password changes as a standard user via `passwd` confirmed `pam_pwquality` enforcement.
- **Container Reachability in Headless ZAP Scans:** Passing `--add-host=host.docker.internal:host-gateway` to `docker run` allowed the ZAP container to reach the host-published application port reliably.

## Quickstart
```bash
mkdir -p ~/cissp-lab/{crypto,reports,app}
cd ~/cissp-lab
uname -a | tee reports/00-env.txt

# Run automated control verification after configuring tasks
chmod +x ~/cissp-lab/validate.sh
~/cissp-lab/validate.sh
