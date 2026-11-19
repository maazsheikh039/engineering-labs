#!/usr/bin/env bash
ok()   { printf '[ OK ] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; }

source /etc/os-release
[[ "$VERSION_ID" == "22.04" ]] && ok "Ubuntu $VERSION_ID" || warn "Expected Ubuntu 22.04, found $PRETTY_NAME"
sudo -n true 2>/dev/null && ok "passwordless sudo" || fail "sudo needs a password or is unavailable"

avail=$(df --output=avail -BG / | tail -n 1 | tr -dc '0-9')
(( avail >= 4 )) && ok "${avail}G free on /" || fail "need at least 4G free on / (have ${avail}G)"

sudo vgs vg_data >/dev/null 2>&1 && fail "volume group vg_data already exists" || ok "no existing vg_data"

for d in /srv/app /srv/applogs /srv/backup /srv/projects; do
  [[ -e $d ]] && warn "$d already exists" || ok "$d is free"
done

ss -ltn | grep -q ':8080' && fail "TCP port 8080 already in use" || ok "TCP port 8080 is free"

for u in alice bob carol dave reportapp; do
  id "$u" >/dev/null 2>&1 && fail "user $u already exists"
done

ok "ufw before lab: $(sudo ufw status | head -n 1)"
ok "CPUs: $(nproc), RAM: $(free -h | awk '/^Mem:/{print $2}')"
