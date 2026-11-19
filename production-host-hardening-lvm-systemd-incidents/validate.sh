#!/usr/bin/env bash
set -u
if [[ $EUID -ne 0 ]]; then echo "Please run with sudo"; exit 1; fi
LAB_USER="${SUDO_USER:-root}"
LAB_HOME="$(getent passwd "$LAB_USER" | cut -d: -f6)"
export LAB_HOME
PASS=0; FAIL=0

check() {
  local desc="$1"; shift
  if "$@" > /dev/null 2>&1; then
    printf '[PASS] %s\n' "$desc"; PASS=$((PASS + 1))
  else
    printf '[FAIL] %s\n' "$desc"; FAIL=$((FAIL + 1))
  fi
}

echo "Task 1 - Users, groups, sudo"
check "groups analysts/devops/auditors exist" getent group analysts devops auditors
check "bob is in analysts" bash -c 'id -nG bob | grep -qw analysts'
check "alice is in devops AND analysts" bash -c 'id -nG alice | grep -qw devops && id -nG alice | grep -qw analysts'
check "alice max password age = 90" bash -c 'chage -l alice | grep -Eq "^Maximum number of days.*: 90$"'
check "carol account has an expiry date" bash -c '! chage -l carol | grep -Eq "^Account expires[[:space:]]*: never$"'
check "sudoers configuration parses" visudo -c
check "alice may restart reportapp" sudo -l -U alice /usr/bin/systemctl restart reportapp.service
check "alice may NOT restart ssh" bash -c '! sudo -l -U alice /usr/bin/systemctl restart ssh.service'

echo "Task 2 - Permissions and ACLs"
check "reports is 2770 root:analysts" bash -c '[ "$(stat -c%a:%U:%G /srv/projects/reports)" = "2770:root:analysts" ]'
check "dropbox is 3770 (setgid+sticky)" bash -c '[ "$(stat -c%a /srv/projects/dropbox)" = "3770" ]'
check "default ACL grants auditors r-x" bash -c 'getfacl -p /srv/projects/reports | grep -qx "default:group:auditors:r-x"'
check "carol can write q2.txt" sudo -u carol test -w /srv/projects/reports/q2.txt
check "dave can read q2.txt" sudo -u dave test -r /srv/projects/reports/q2.txt
check "dave cannot write q2.txt" bash -c '! sudo -u dave test -w /srv/projects/reports/q2.txt'

echo "Task 3 - Storage"
check "vg_data has 2 PVs" bash -c '[ "$(vgs --noheadings -o pv_count vg_data | tr -d " ")" = "2" ]'
check "lv_app is at least 790 MiB" bash -c 'lvs --noheadings --units m --nosuffix -o lv_size vg_data/lv_app | awk "{ exit !(\$1 >= 790) }"'
check "/srv/app mounted (ext4)" bash -c 'findmnt -n -o FSTYPE /srv/app | grep -qx ext4'
check "/srv/applogs mounted (xfs)" bash -c 'findmnt -n -o FSTYPE /srv/applogs | grep -qx xfs'
check "/srv/backup mounted noexec" bash -c 'findmnt -n -o OPTIONS /srv/backup | grep -q noexec'
check "3 UUID entries in /etc/fstab" bash -c '[ "$(grep -cE "^UUID=.*/srv/(app|applogs|backup)[[:space:]]" /etc/fstab)" = "3" ]'
check "lab-loopdisks.service enabled" systemctl is-enabled --quiet lab-loopdisks.service

echo "Task 4 - systemd service"
check "reportapp.service active" systemctl is-active --quiet reportapp.service
check "reportapp.service enabled" systemctl is-enabled --quiet reportapp.service
check "/health returns ok" bash -c 'curl -fsS -m 5 http://127.0.0.1:8080/health | grep -q "\"status\": \"ok\""'
check "log dir owned by reportapp" bash -c '[ "$(stat -c%U /srv/applogs/reportapp)" = "reportapp" ]'
check "MemoryMax drop-in applied (200M)" bash -c '[ "$(systemctl show -p MemoryMax --value reportapp.service)" = "209715200" ]'
check "report-summary finds 3 reports" bash -c '/usr/local/bin/report-summary | grep -q "3 report(s), 114 bytes"'

echo "Task 5 - Network, SSH, firewall"
check "ufw is active" bash -c 'ufw status | grep -q "^Status: active"'
check "sshd: permitrootlogin no" bash -c 'sshd -T | grep -qx "permitrootlogin no"'
check "sshd: maxauthtries 3" bash -c 'sshd -T | grep -qx "maxauthtries 3"'
check "ufw: 8080/tcp only from 192.168.77.0/24" bash -c 'ufw status | grep -Eq "^8080/tcp +ALLOW +192\.168\.77\.0/24"'
check "LAN namespace reaches reportapp" ip netns exec client curl -fsS -m 5 http://192.168.77.1:8080/health

echo "Task 6 - Logs and logrotate"
check "logrotate uses copytruncate" grep -Eq '^[[:space:]]*copytruncate' /etc/logrotate.d/reportapp
check "logrotate config has no errors" bash -c '! logrotate -d /etc/logrotate.d/reportapp 2>&1 | grep -qi "^error"'
check "report: 3050 requests in sample" bash -c '/usr/local/bin/reportapp-traffic-report "$LAB_HOME/lab/access-sample.log" | grep -q "Total requests: 3050"'
check "report: 5xx rate 4.92%" bash -c '/usr/local/bin/reportapp-traffic-report "$LAB_HOME/lab/access-sample.log" | grep -q "5xx error rate: 4.92%"'
check "report: exit 2 on unreadable file" bash -c '/usr/local/bin/reportapp-traffic-report /nonexistent.log; [ $? -eq 2 ]'

echo "Task 7 - Automation"
check "backup timer enabled" systemctl is-enabled --quiet reportapp-backup.timer
check "backup timer active" systemctl is-active --quiet reportapp-backup.timer
check "1 to 5 archives retained" bash -c 'n=$(ls /srv/backup/archive/reportapp-*.tar.gz 2>/dev/null | wc -l); [ "$n" -ge 1 ] && [ "$n" -le 5 ]'
check "newest archive checksum valid" bash -c 'f=$(ls -1t /srv/backup/archive/reportapp-*.tar.gz | head -n 1); sha256sum -c "$f.sha256"'
check "cron.d job every 15 min as reportapp" grep -Eq '^\*/15 \* \* \* \* reportapp' /etc/cron.d/reportapp-report

echo "Task 8 - Performance and incidents"
check "no runaway report-indexer processes" bash -c '! pgrep -x report-indexer'
check "report-exporter not running" bash -c '! systemctl is-active --quiet report-exporter.service'
check "no deleted-but-open files on /srv/app" bash -c '! lsof +L1 /srv/app'
check "sysstat collection enabled" grep -q '^ENABLED="true"' /etc/default/sysstat

echo
echo "Result: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
