#!/usr/bin/env bash
set -euo pipefail

# Read-only system audit: generates a Markdown report and bundles key configs.
# Outputs:
#   - ~/pi-change-report.md
#   - ~/pi-change-bundle.tar.gz (includes copies of key config files)

# Resolve output paths for the calling user (supports sudo)
if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
  USER_DIR="/home/$SUDO_USER"
else
  USER_DIR="$HOME"
fi
TS="$(date -Iseconds)"
OUT_MD="$USER_DIR/pi-change-report.md"
OUT_DIR="$USER_DIR/pi-change-bundle"
mkdir -p "$OUT_DIR"

section() { printf "\n**%s**\n" "$1"; }
trim() { awk 'NR<=400{print} NR==401{print "...(trimmed)"}'; }

copy_if_exists() {
  local f="$1"
  if [[ -f "$f" ]]; then
    cp -n "$f" "$OUT_DIR/" 2>/dev/null || true
  fi
}

wlan_interfaces() {
  # Prefer iw; fallback to sysfs
  if command -v iw >/dev/null 2>&1; then
    iw dev | awk '/Interface/ {print $2}'
  else
    ls /sys/class/net 2>/dev/null | grep -E '^wl' || true
  fi
}

wlan_info_block() {
  local iface="$1"
  echo "### WLAN Interface: $iface"
  echo "Link + address:"
  ip -brief addr show "$iface" 2>/dev/null || true
  echo
  if command -v iw >/dev/null 2>&1; then
    echo "iw dev $iface info:"; iw dev "$iface" info 2>/dev/null | trim || true; echo
    echo "iw dev $iface link:"; iw dev "$iface" link 2>/dev/null | trim || true; echo
  fi
  if command -v iwconfig >/dev/null 2>&1; then
    echo "iwconfig $iface:"; iwconfig "$iface" 2>/dev/null | trim || true; echo
  fi
}

# Generate Markdown report
{
  echo "# Pi Change Report"
  echo "- Generated: $TS"
  echo

  section "OS"
  uname -a
  echo
  hostnamectl 2>/dev/null || true
  echo
  sed -n '1,120p' /etc/os-release 2>/dev/null || true

  section "Uptime"
  who -b 2>/dev/null || true
  last reboot -n 3 2>/dev/null || true

  section "Network Interfaces & IPs"
  ip -brief link 2>/dev/null || true
  echo
  ip -brief addr 2>/dev/null || true

  section "Wireless (WLAN)"
  if command -v rfkill >/dev/null 2>&1; then
    echo "rfkill:"; rfkill list 2>/dev/null | trim || true; echo
  fi
  if command -v iw >/dev/null 2>&1; then
    echo "iw reg get:"; iw reg get 2>/dev/null | trim || true; echo
    echo "iw list (caps):"; iw list 2>/dev/null | trim || true; echo
  fi
  for w in $(wlan_interfaces); do
    wlan_info_block "$w"
    echo
  done

  section "Routing & Policy"
  echo "Routes (all tables):"; ip route show table all 2>/dev/null | trim || true
  echo
  echo "Rules:"; ip rule 2>/dev/null | trim || true

  section "Listeners (TCP/UDP)"
  echo "TCP:"; ss -ltnp 2>/dev/null | trim || true
  echo
  echo "UDP:"; ss -lunp 2>/dev/null | trim || true

  section "Firewall / NAT"
  echo "iptables (filter):"; iptables -S 2>/dev/null | trim || echo "iptables not present"; echo
  echo "iptables (nat):"; iptables -t nat -S 2>/dev/null | trim || true; echo
  if command -v nft >/dev/null 2>&1; then
    echo "nftables ruleset:"; nft list ruleset 2>/dev/null | trim || true; echo
  fi
  echo "sysctl forwarding:"; sysctl net.ipv4.ip_forward 2>/dev/null || true; echo

  section "Services (enabled)"
  systemctl list-unit-files --state=enabled 2>/dev/null | trim || true
  echo
  section "Services (running)"
  systemctl --type=service --state=running 2>/dev/null | trim || true
  echo

  section "Key Service Status"
  for svc in nginx apache2 dnsmasq hostapd; do
    echo "== $svc =="
    systemctl is-enabled "$svc" 2>/dev/null || true
    systemctl is-active "$svc" 2>/dev/null || true
    systemctl status "$svc" --no-pager 2>/dev/null | trim || true
    echo
  done

  section "APT / Packages"
  echo "Sources:"; grep -Rhv '^#' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null || true
  echo
  echo "Manual packages (apt-mark showmanual):"; apt-mark showmanual 2>/dev/null | sort | trim || true
  echo
  echo "Recent APT history:"; tail -n 200 /var/log/apt/history.log 2>/dev/null | trim || echo "No history.log"; echo
  echo "Recent dpkg log:"; tail -n 200 /var/log/dpkg.log 2>/dev/null | trim || echo "No dpkg.log"; echo

  section "Package Configs Changed (dpkg -V)"
  echo "Note: Lines indicate files differing from package defaults."; dpkg -V 2>/dev/null | trim || echo "dpkg -V had no output or not supported"; echo

  section "DNS"
  echo "/etc/resolv.conf:"; sed -n '1,120p' /etc/resolv.conf 2>/dev/null || true; echo
  echo "/etc/hosts:"; sed -n '1,120p' /etc/hosts 2>/dev/null || true; echo

  section "Nginx"
  nginx -t 2>&1 | trim || true; echo
  ls -l /etc/nginx/conf.d 2>/dev/null || true; echo
  for f in /etc/nginx/conf.d/*.conf /etc/nginx/sites-enabled/*; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"; sed -n '1,200p' "$f" | trim; echo
    copy_if_exists "$f"
  done

  section "Apache (presence only)"
  dpkg -l | awk '/^ii\s+apache2/{print $0}' 2>/dev/null || true
  ls -l /etc/apache2 2>/dev/null || true
  [[ -f /etc/apache2/ports.conf ]] && { echo "/etc/apache2/ports.conf:"; sed -n '1,120p' /etc/apache2/ports.conf | trim; echo; }

  section "hostapd / dhcpcd / dnsmasq"
  if [[ -f /etc/hostapd/hostapd.conf ]]; then
    echo "/etc/hostapd/hostapd.conf:"; sed -n '1,200p' /etc/hostapd/hostapd.conf | trim; echo
    copy_if_exists /etc/hostapd/hostapd.conf
  fi
  if [[ -f /etc/default/hostapd ]]; then
    echo "/etc/default/hostapd:"; sed -n '1,200p' /etc/default/hostapd | trim; echo
    copy_if_exists /etc/default/hostapd
  fi
  if [[ -f /etc/dhcpcd.conf ]]; then
    echo "/etc/dhcpcd.conf:"; sed -n '1,200p' /etc/dhcpcd.conf | trim; echo
    copy_if_exists /etc/dhcpcd.conf
  fi
  for f in /etc/dnsmasq.conf /etc/dnsmasq.d/*.conf; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"; sed -n '1,200p' "$f" | trim; echo
    copy_if_exists "$f"
  done

  section "sysctl"
  [[ -f /etc/sysctl.conf ]] && { echo "/etc/sysctl.conf:"; sed -n '1,200p' /etc/sysctl.conf | trim; echo; copy_if_exists /etc/sysctl.conf; }
  for f in /etc/sysctl.d/*.conf; do
    [[ -f "$f" ]] || continue
    echo "--- $f ---"; sed -n '1,200p' "$f" | trim; echo
    copy_if_exists "$f"
  done

  section "Cron"
  echo "System cron dirs:"; ls -l /etc/cron.* 2>/dev/null || true; echo
  echo "Root crontab:"; crontab -l 2>/dev/null | trim || echo "No root crontab"; echo

  section "Logs (recent)"
  echo "hostapd journal (last 100 lines):"; journalctl -u hostapd -n 100 --no-pager 2>/dev/null | trim || true; echo
  echo "nginx journal (last 100 lines):"; journalctl -u nginx -n 100 --no-pager 2>/dev/null | trim || true; echo
} >"$OUT_MD"

# Bundle the report and copied configs
if command -v tar >/dev/null 2>&1; then
  tar -C "$USER_DIR" -czf "$USER_DIR/pi-change-bundle.tar.gz" "$(basename "$OUT_MD")" "$(basename "$OUT_DIR")" 2>/dev/null || true
fi

echo "Report: $OUT_MD"
echo "Bundle: $USER_DIR/pi-change-bundle.tar.gz"