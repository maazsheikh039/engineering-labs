# AcmeWidgets host firewall policy
default-in: deny
default-out: allow
rule: allow 22/tcp rate-limited (brute-force mitigation)
rule: allow 3000/tcp from 127.0.0.1 only (internal web app)
