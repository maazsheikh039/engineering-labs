#!/usr/bin/env bash
set -u

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; }

# Task 1
getfacl /var/log/appdemo/app.log 2>/dev/null | grep -q 'group:appops:r--' \
  && pass "T1 ACL read-only for appops" || fail "T1 ACL"
sudo visudo -c -f /etc/sudoers.d/90-appops 2>/dev/null | grep -q 'parsed OK' \
  && pass "T1 sudoers valid" || fail "T1 sudoers"

# Task 2
grep -q 'minlen = 12' /etc/security/pwquality.conf \
  && pass "T2 pwquality minlen" || fail "T2 pwquality"
[ "$(grep -c pam_faillock /etc/pam.d/common-auth)" -ge 3 ] \
  && pass "T2 faillock stack" || fail "T2 faillock"

# Task 3
openssl verify -CAfile ~/cissp-lab/crypto/ca.crt ~/cissp-lab/crypto/app.crt 2>/dev/null \
  | grep -q OK && pass "T3 cert chain" || fail "T3 cert chain"
echo "release 1.0.0 build artefact" > ~/cissp-lab/crypto/release.tar.contents
gpg --verify ~/cissp-lab/crypto/release.sig ~/cissp-lab/crypto/release.tar.contents 2>&1 \
  | grep -q "Good signature" && pass "T3 gpg signature" || fail "T3 gpg signature"
test -f ~/cissp-lab/crypto/app-secrets.enc \
  && pass "T3 encrypted secret" || fail "T3 encrypted secret"

# Task 4
sudo auditctl -l 2>/dev/null | grep -q identity \
  && pass "T4 audit rules loaded" || fail "T4 audit rules"

# Task 5
sudo ufw status 2>/dev/null | grep -q "Status: active" \
  && pass "T5 ufw active" || fail "T5 ufw"
sudo ufw status 2>/dev/null | grep -q "22/tcp" \
  && pass "T5 SSH allowed" || fail "T5 SSH rule"

# Task 6
test -f ~/cissp-lab/reports/oscap-arf.xml \
  && pass "T6 openscap results" || fail "T6 openscap"
sudo grep -qi "Hardening index" /var/log/lynis.log \
  && pass "T6 lynis score" || fail "T6 lynis"

# Task 7
test -s ~/cissp-lab/reports/trivy-juiceshop.txt \
  && pass "T7 trivy report" || fail "T7 trivy"
test -f ~/cissp-lab/reports/zap/zap-baseline-report.json \
  && pass "T7 zap report" || fail "T7 zap"
docker ps --filter name=juiceshop --format '{{.Names}}' | grep -q juiceshop \
  && pass "T7 juiceshop running" || fail "T7 juiceshop"
