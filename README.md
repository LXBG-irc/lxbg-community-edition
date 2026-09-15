# LXBG Community Edition 1.0

Free starter edition of the LXBG IRC stack for running your own independent IRC community.

Included:
- LXBGIRCd 1.0 (Linux amd64)
- TLS IRC and classic IRC client support
- IRCv3 CAP + SASL PLAIN authentication bridge
- Web account/register/login starter UI
- Channel registration and role schema
- WebSocket bridge for browser clients
- Database schema for accounts, nicknames, channels and CAM permissions
- systemd templates and installer

## Requirements
Fresh Debian 12 / Ubuntu 24.04 style Linux server, root access, MariaDB/MySQL, PHP 8.2+, Python 3, nginx or another web server, and a TLS certificate for your IRC hostname.

## Quick start
1. Copy this folder to `/opt/lxbg-ce`.
2. Copy `config.example.json` to `config.json` and enter your database settings.
3. Create a database and import `schema.sql`.
4. Point your web server at `web/` for the starter account/channel UI.
5. Set the environment values shown in `systemd/lxbg-ircd.service.example`.
6. Install/start the auth bridge first, then LXBGIRCd, then the WebSocket bridge.

Or run `sudo ./install.sh` after reviewing its variables. The installer is intentionally conservative: it will not install packages, configure DNS, request certificates or open firewall ports automatically.

## Default ports
- IRC: 6667
- IRC TLS: 6697
- WebSocket bridge: 8000 (localhost; reverse proxy it as WSS)

## Security
Do not expose `config.json`, database credentials, auth sockets, or state files through the web root. Use TLS for public IRC. Change all example values before production use.

## Project
Live project and demo: https://lxbg.de/launch.php
