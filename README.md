# LXBG Community Edition

**Real IRC. Modern web. Self-hosted.**

LXBG Community Edition is a self-hosted IRC community platform built around **LXBGIRCd 1.0**, with classic IRC client support plus a browser-first community experience.

The project grew from an IRC community originally operated around 2005. The goal is not to replace IRC with another closed chat platform, but to bring independent IRC communities into the modern web while keeping real IRC underneath.

## Features

- LXBGIRCd 1.0 IRC daemon
- Classic IRC client compatibility
- TLS and SASL authentication
- Browser accounts and web chat starter UI
- Channels and permission foundations
- WebSocket bridge for browser IRC connectivity
- WebRTC webcam foundations for community experiences
- SQL schema and example configuration
- systemd service templates
- Conservative Linux installer

## Quick start

Requirements: Linux amd64, MySQL/MariaDB, PHP 8+, Python 3 and systemd.

```bash
unzip LXBG-Community-Edition-1.0.zip
cd LXBG-Community-Edition-1.0
cp config.example.json config.json
```

Create a database, import `schema.sql`, edit `config.json`, review the installer and then run:

```bash
sudo ./install.sh
```

The installer intentionally does **not** configure DNS, firewall rules, public TLS certificates or automatically expose services to the internet. Review `docs/INSTALL.md` before deployment.

## Repository layout

| Path | Purpose |
| --- | --- |
| `bin/` | LXBGIRCd Linux amd64 binary |
| `services/` | Authentication and WebSocket/service components |
| `web/` | Starter community web interface |
| `systemd/` | Example service units |
| `schema.sql` | Community Edition database schema |
| `config.example.json` | Safe example configuration |
| `docs/INSTALL.md` | Installation guide |

## Community Edition

This repository is the free Community Edition starter build. It is intended for self-hosters, testers and people interested in running independent IRC infrastructure. It is not a turnkey copy of the production lxbg.de environment.

Project page and packaged download: https://lxbg.de/community-edition.php?src=github

Live community: https://lxbg.de/?src=github

## Feedback and contributions

Issues are welcome for bugs, installation feedback and compatibility reports. The project is young, so reports from IRC operators, self-hosters and networking enthusiasts are especially useful.

A future module ecosystem is planned so independently developed extensions can be installed without modifying the core.

## Security

Never commit production credentials, private keys, certificates or `config.json`. The repository `.gitignore` excludes common local secret files. For security-sensitive reports, avoid posting credentials or exploitable private infrastructure details in public issues.

## License

No open-source license is granted by this repository yet. The Community Edition is distributed as a free-to-use starter edition under its accompanying project terms. A formal source/module licensing model will be published separately.
