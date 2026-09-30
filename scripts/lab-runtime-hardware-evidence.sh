#!/usr/bin/env bash
set -euo pipefail

# Read-only lab evidence collector for issue #195.
# Default mode does not install packages, mutate services, run fsck, or enable Runner MCP.
# Optional bounded guest-memory stress: RUN_STRESS=1 bash scripts/lab-runtime-hardware-evidence.sh

echo "=== AIFORDABLE LAB HOST/RUNTIME EVIDENCE ==="
date --iso-8601=seconds
echo

echo "=== VIRTUALIZATION / CPU ==="
uname -srmo
systemd-detect-virt || true
lscpu | grep -E '^(Architecture|CPU\(s\)|Model name|Vendor ID|Virtualization|Hypervisor vendor):' || true
echo

echo "=== MEMORY ==="
free -h
grep -E '^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree|HardwareCorrupted):' /proc/meminfo || true
echo

echo "=== ROOT FILESYSTEM ==="
findmnt -no FSTYPE,OPTIONS / || true
df -hT /
echo

echo "=== PYTHON PACKAGE INTEGRITY ==="
command -v python3.12 || true
python3.12 --version || true
sha256sum /usr/bin/python3.12 2>/dev/null || true
dpkg -V python3.12-minimal python3.12 libpython3.12-minimal libpython3.12-stdlib 2>&1 || true
echo

echo "=== KERNEL HARDWARE / MEMORY EVIDENCE (CURRENT BOOT) ==="
journalctl -k -b --no-pager 2>/dev/null |   grep -Eai 'machine check|mce:|hardware error|edac|ecc|memory failure|memory error|page.*poison|uncorrect(ed|able)|corrected error|ras:' |   tail -n 200 || true
echo

echo "=== KERNEL STORAGE / FILESYSTEM EVIDENCE (CURRENT BOOT) ==="
journalctl -k -b --no-pager 2>/dev/null |   grep -Eai 'I/O error|blk_update_request|buffer I/O|nvme.*(error|reset|abort|timeout)|ata.*(error|failed|timeout)|EXT4-fs.*error|XFS.*error|BTRFS.*error|filesystem.*corrupt|read-only filesystem' |   tail -n 200 || true
echo

echo "=== RECENT SEGFAULT / GENERAL PROTECTION EVIDENCE ==="
journalctl -k --since '-24 hours' --no-pager 2>/dev/null |   grep -Eai 'segfault|general protection|trap invalid opcode|machine check|hardware error' |   tail -n 200 || true
echo

echo "=== FAILED SERVICES ==="
systemctl --failed --no-legend --plain 2>/dev/null || true
echo

if [[ "${RUN_STRESS:-0}" == "1" ]]; then
  echo "=== OPTIONAL BOUNDED GUEST MEMORY STRESS ==="
  if command -v stress-ng >/dev/null 2>&1; then
    # Guest-only stress: useful for reproduction, not proof that physical RAM is healthy.
    timeout 12m stress-ng --vm 4 --vm-bytes 75% --verify --timeout 10m --metrics-brief
  elif command -v memtester >/dev/null 2>&1; then
    echo "memtester is installed, but this script will not guess a safe memory size or invoke sudo."
    echo "Run memtester manually from a maintenance window if desired."
  else
    echo "SKIP: neither stress-ng nor memtester is installed."
  fi
  echo
fi

echo "=== IMPORTANT ==="
echo "A clean guest run does NOT prove physical RAM/CPU/storage health."
echo "For the Hyper-V host, verify current BIOS/microcode/default CPU settings and run an offline physical RAM test."
echo "Do not enable Runner MCP autostart/mailbox/Agent Bus until runtime qualification is clear."
