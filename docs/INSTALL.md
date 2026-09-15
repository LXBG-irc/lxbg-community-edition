# Installation

## 1. Database
Create an empty UTF-8 MariaDB/MySQL database and a dedicated database user. Import `schema.sql`.

## 2. Configuration
Copy `config.example.json` to `config.json`. Fill in the DB host, port, username, password and database. Keep the file mode 600 and outside the public web root.

## 3. Web starter UI
Serve `web/` with PHP 8.2+. Adjust the bootstrap/config path if your layout differs. Use HTTPS.

## 4. Auth bridge
Run `services/auth_bridge.py` with:
`LXBG_AUTH_SOCKET=/run/lxbg-ce/auth.sock`
`LXBG_SERVICES_CONFIG=/opt/lxbg-ce/config.json`

## 5. IRCd
Run `bin/lxbgircd-linux-amd64` with environment variables:
`LXBG_SERVER_NAME=irc.example.org`
`LXBG_IRC_ADDR=0.0.0.0:6667`
`LXBG_TLS_ADDR=0.0.0.0:6697`
`LXBG_TLS_CERT=/path/fullchain.pem`
`LXBG_TLS_KEY=/path/privkey.pem`
`LXBG_AUTH_SOCKET=/run/lxbg-ce/auth.sock`
`LXBG_STATE_FILE=/var/lib/lxbg-ce/state.json`

## 6. Browser bridge
Run `services/ws_bridge.py` on localhost and reverse proxy `/irc-ws/` with WebSocket upgrade headers.

## 7. Test
Use any IRC client to connect over TLS and confirm the server returns `LXBGIRCd-1.0` to `/VERSION`.
