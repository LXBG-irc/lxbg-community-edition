#!/usr/bin/env bash
set -euo pipefail
PREFIX=${PREFIX:-/opt/lxbg-ce}
USER_NAME=${LXBG_USER:-lxbg}
if [ "$(id -u)" -ne 0 ]; then echo "Run as root." >&2; exit 1; fi
for x in python3 systemctl; do command -v "$x" >/dev/null || { echo "Missing requirement: $x" >&2; exit 1; }; done
if ! id "$USER_NAME" >/dev/null 2>&1; then useradd --system --home "$PREFIX" --shell /usr/sbin/nologin "$USER_NAME"; fi
SRC=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$PREFIX" /run/lxbg-ce /var/lib/lxbg-ce
cp -a "$SRC"/. "$PREFIX"/
[ -f "$PREFIX/config.json" ] || cp "$PREFIX/config.example.json" "$PREFIX/config.json"
chown -R "$USER_NAME:$USER_NAME" "$PREFIX" /run/lxbg-ce /var/lib/lxbg-ce
chmod 600 "$PREFIX/config.json"
chmod +x "$PREFIX/bin/lxbgircd-linux-amd64"
echo "LXBG CE installed to $PREFIX"
echo "NEXT: edit $PREFIX/config.json, import schema.sql, review systemd examples and TLS paths."
echo "The installer did NOT start public services automatically."
