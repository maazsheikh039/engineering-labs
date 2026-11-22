#!/usr/bin/env bash
# validate.sh - final check for RHEL/AlmaLinux SysOps lab (run on Ubuntu host)
set -u
PASS=0
FAIL=0

check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '[PASS] %s\n' "$desc"
    PASS=$((PASS + 1))
  else
    printf '[FAIL] %s\n' "$desc"
    FAIL=$((FAIL + 1))
  fi
}

on_app() { docker exec app01 bash -c "$1"; }
on_bkp() { docker exec bkp01 bash -c "$1"; }
lv_mb() { sudo lvs --noheadings --units m --nosuffix -o lv_size "vg_lab/$1" 2>/dev/null | awk '{printf "%d", $1}'; }
pv_count() { sudo vgs --noheadings -o pv_count vg_lab 2>/dev/null | tr -d ' '; }

echo "Task 1 LVM storage on loop devices"
check "volume group vg_lab exists" sudo vgs vg_lab
check "lv_backup is XFS mounted on /srv/rhel-lab/backup" bash -c '[ "$(findmnt -n -o FSTYPE /srv/rhel-lab/backup)" = xfs ]'
check "/etc/fstab mounts the backup LV by UUID" grep -Eq '^UUID=[0-9a-f-]+[[:space:]]+/srv/rhel-lab/backup[[:space:]]+xfs' /etc/fstab
check "lv_swap is active swap" bash -c 'swapon --show=NAME --noheadings | grep -qx "$(readlink -f /dev/vg_lab/lv_swap)"'

echo "Task 2 systemd servers"
check "app01 is running" bash -c '[ "$(docker inspect -f "{{.State.Running}}" app01)" = true ]'
check "bkp01 is running" bash -c '[ "$(docker inspect -f "{{.State.Running}}" bkp01)" = true ]'
check "app01 is Rocky Linux 9 with systemd up" on_app 'grep -q "Rocky Linux 9" /etc/os-release && systemctl is-system-running | grep -Eqx "running|degraded"'
check "bkp01 is AlmaLinux 9 with systemd up" on_bkp 'grep -q "AlmaLinux 9" /etc/os-release && systemctl is-system-running | grep -Eqx "running|degraded"'
check "bkp01 sees the XFS volume at /backup" on_bkp '[ "$(findmnt -n -o FSTYPE /backup)" = xfs ]'

echo "Task 3 software management"
check "httpd installed" on_app 'rpm -q httpd'
check "localrepo enabled with gpgcheck = 1" on_app 'dnf -q repolist --enabled | grep -qw localrepo && grep -Eq "^gpgcheck[[:space:]]*=[[:space:]]*1" /etc/yum.repos.d/localrepo.repo'
check "tree installed from localrepo" on_app 'dnf list installed tree 2>/dev/null | grep -q "@localrepo"'

echo "Task 4 users, sudo, ACLs"
check "alice in webdev, max age 90" on_app 'id -nG alice | grep -qw webdev && chage -l alice | grep -Eq "^Maximum.*: 90$"'
check "carol in webdev and auditors" on_app 'id -nG carol | grep -qw webdev && id -nG carol | grep -qw auditors'
check "carol account expires 2030" on_app 'chage -l carol | grep -q "Account expires.*2030"'
check "dave is locked" on_app 'passwd -S dave | grep -qw LK'
check "webdeploy has nologin shell" on_app 'getent passwd webdeploy | grep -q /sbin/nologin'
check "default ACL gives webdev rwx" on_app 'getfacl -p /srv/webcontent | grep -qx "default:group:webdev:rwx"'
check "setgid set on /srv/webcontent" on_app '[ -g /srv/webcontent ]'
check "sudoers valid and alice may restart httpd" on_app 'visudo -c && sudo -l -U alice | grep -q "systemctl restart httpd"'

echo "Task 5 services and journal"
check "httpd active and enabled" on_app 'systemctl is-active httpd && systemctl is-enabled httpd'
check "httpd drop-in Restart=on-failure" on_app '[ "$(systemctl show -p Restart --value httpd)" = on-failure ]'
check "portal answers on port 82" on_app 'curl -s http://localhost:82/ | grep -q "Acme Internal Portal"'
check "journal is persistent" on_app 'ls /var/log/journal/*/system.journal'
check "SELinux runbook valid" on_app 'bash -n /root/selinux-httpd-runbook.sh && grep -q "http_port_t -p tcp 82" /root/selinux-httpd-runbook.sh && grep -q "restorecon" /root/selinux-httpd-runbook.sh'

echo "Task 6 firewall and networking"
check "firewalld running" on_app 'firewall-cmd --state'
check "acme-portal service maps to 82/tcp" on_app 'firewall-cmd --permanent --service=acme-portal --get-ports | grep -qw "82/tcp"'
check "public allows http and acme-portal" on_app 'S=$(firewall-cmd --zone=public --list-services); echo "$S" | grep -qw http && echo "$S" | grep -qw acme-portal'
check "ssh not open to everyone" on_app '! firewall-cmd --zone=public --list-services | grep -qw ssh'
check "rich rule allows ssh from bkp01" on_app 'firewall-cmd --zone=public --list-rich-rules | grep -q "172.30.0.20"'
check "bkp01 reaches the portal" on_bkp 'curl -s -m 5 http://app01:82/ | grep -q "Acme Internal Portal"'
check "mgmt0 connection activated" on_app 'nmcli -t -f GENERAL.STATE connection show mgmt0 | grep -q activated'
check "dummy0 is in the internal zone" on_app '[ "$(firewall-cmd --get-zone-of-interface=dummy0)" = internal ]'

echo "Task 7 SSH and backups"
check "sshd active" on_app 'systemctl is-active sshd'
check "root login disabled" on_app 'sshd -T | grep -qx "permitrootlogin no"'
check "password auth disabled" on_app 'sshd -T | grep -qx "passwordauthentication no"'
check "key login bkp01 -> app01" on_bkp 'su -s /bin/bash bkpsvc -c "ssh -o BatchMode=yes bkpsvc@app01 true"'
check "backup timer enabled and active" on_bkp 'systemctl is-enabled app01-backup.timer && systemctl is-active app01-backup.timer'
check "at least one archive exists" on_bkp 'ls /backup/app01/archive/app01-*.tar.gz'
check "retention cron job installed" on_bkp 'grep -q "mtime +7" /etc/cron.d/app01-backup-retention'
check "bkpsvc user crontab installed" on_bkp 'crontab -l -u bkpsvc | grep -q "df -h /backup"'

echo "Task 8 online extension"
check "vg_lab spans at least 2 PVs" test "$(pv_count)" -ge 2
check "lv_backup is at least 1100 MiB" test "$(lv_mb lv_backup)" -ge 1100
check "lv_swap is at least 190 MiB" test "$(lv_mb lv_swap)" -ge 190
check "bkp01 sees the larger filesystem" on_bkp '[ "$(df -m --output=size /backup | tail -1 | tr -d " ")" -ge 1000 ]'

echo
echo "RESULT: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ]
