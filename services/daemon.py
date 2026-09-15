#!/usr/bin/env python3
import argparse, asyncio, base64, json, logging, time
from dataclasses import dataclass, field
from pathlib import Path
import pymysql
from argon2 import PasswordHasher, exceptions as argon2_exc

VERSION = "1.0.0-dev1"

@dataclass
class Config:
    server_name: str
    sid: str
    description: str
    irc_host: str
    irc_port: int
    irc_password: str
    db: dict
    service_nicks: dict = field(default_factory=lambda: {"NickServ":"Nickname Service","ChanServ":"Channel Service"})

    @classmethod
    def load(cls, path: str):
        raw = json.loads(Path(path).read_text())
        return cls(
            server_name=raw["irc"]["server_name"],
            sid=raw["irc"]["sid"],
            description=raw["irc"].get("description", "LXBG Services"),
            irc_host=raw["irc"]["host"],
            irc_port=int(raw["irc"]["port"]),
            irc_password=raw["irc"]["password"],
            db=raw["database"],
            service_nicks=raw.get("service_nicks", {"NickServ":"Nickname Service","ChanServ":"Channel Service"}),
        )

class Database:
    def __init__(self, cfg): self.cfg = cfg
    def connect(self):
        return pymysql.connect(
            host=self.cfg["host"], port=int(self.cfg.get("port", 3306)),
            user=self.cfg["username"], password=self.cfg["password"],
            database=self.cfg["database"], charset="utf8mb4", autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )
    def ping(self):
        with self.connect() as c, c.cursor() as q:
            q.execute("SELECT VERSION() AS v, DATABASE() AS db")
            return q.fetchone()
    def nickname_owner(self, nick):
        with self.connect() as c, c.cursor() as q:
            q.execute("SELECT n.id,n.user_id,n.nickname,a.status FROM ls_nicknames n JOIN ls_users a ON a.id=n.user_id WHERE n.nickname_normalized=%s LIMIT 1", (nick.lower(),))
            return q.fetchone()
    def authenticate(self, identity, password):
        with self.connect() as c, c.cursor() as q:
            q.execute("""SELECT DISTINCT u.id,u.username,u.password_hash,u.status
                         FROM ls_users u
                         LEFT JOIN ls_nicknames n ON n.user_id=u.id
                         WHERE u.status='active' AND (u.username_normalized=%s OR n.nickname_normalized=%s)
                         LIMIT 1""", (identity.lower(), identity.lower()))
            row=q.fetchone()
            if not row:
                return None
            try:
                PasswordHasher().verify(row['password_hash'], password)
                return row
            except (argon2_exc.VerifyMismatchError, argon2_exc.VerificationError, argon2_exc.InvalidHashError):
                return None

    def channel(self, name):
        with self.connect() as c, c.cursor() as q:
            q.execute("SELECT id,channel_name AS name,founder_user_id,is_active AS status FROM ls_channels WHERE channel_name_normalized=%s LIMIT 1", (name.lower(),))
            return q.fetchone()

class IRCMessage:
    def __init__(self, line):
        self.raw=line; self.prefix=None; self.command=""; self.params=[]
        rest=line.rstrip("\r\n")
        if rest.startswith(":"):
            self.prefix, rest = rest[1:].split(" ", 1)
        if " :" in rest:
            head, trailing = rest.split(" :", 1); bits=head.split(); bits.append(trailing)
        else:
            bits=rest.split()
        if bits:
            self.command=bits.pop(0).upper(); self.params=bits

class LXBGServices:
    def __init__(self, cfg, db):
        self.cfg=cfg; self.db=db; self.reader=None; self.writer=None
        self.uid_counter=0; self.users={}; self.nick_to_uid={}; self.service_uids={}; self.uplink_sid=None; self.sasl_sessions={}

    async def send(self, line):
        logging.debug("-> %s", "PASS :***" if line.startswith("PASS ") else line)
        self.writer.write((line+"\r\n").encode()); await self.writer.drain()

    def next_uid(self):
        self.uid_counter += 1
        return self.cfg.sid + f"{self.uid_counter:06X}"[-6:]

    async def introduce_service(self, nick, gecos):
        uid=self.next_uid(); now=int(time.time())
        await self.send(f"UID {nick} 1 {now} services {self.cfg.server_name} {uid} 0 +ioS * * * :{gecos}")
        self.service_uids[nick]=uid

    async def handshake(self):
        await self.send(f"PASS :{self.cfg.irc_password}")
        await self.send(f"PROTOCTL EAUTH={self.cfg.server_name} SID={self.cfg.sid}")
        await self.send("PROTOCTL NOQUIT NICKv2 SJOIN SJ3 CLK TKLEXT TKLEXT2 NEXTBANS NICKIP ESVID MLOCK EXTSWHOIS")
        await self.send(f"SERVER {self.cfg.server_name} 1 :{self.cfg.description} {VERSION}")

    async def notice(self, service, target, text):
        src=self.service_uids.get(service, service)
        await self.send(f":{src} NOTICE {target} :{text}")

    async def sasl_send(self, server, puid, kind, data):
        src=self.service_uids.get("LXNickServ", self.cfg.sid)
        await self.send(f":{src} SASL {server} {puid} {kind} {data}")

    async def sasl_finish(self, server, puid, ok, account=None):
        src=self.service_uids.get("LXNickServ", self.cfg.sid)
        if ok and account:
            await self.send(f":{src} SVSLOGIN {server} {puid} :{account}")
            await self.sasl_send(server, puid, "D", "S")
        else:
            await self.sasl_send(server, puid, "D", "F")
        self.sasl_sessions.pop(puid, None)

    async def handle_sasl(self, m):
        # Unreal S2S: SASL <target-services> <puid> <S|C|D> <data>
        if len(m.params) < 3:
            return
        # Depending on routing/version the target services name may be omitted on receive.
        if len(m.params) >= 4:
            target,puid,kind,data=m.params[0],m.params[1],m.params[2],m.params[3]
        else:
            puid,kind,data=m.params[0],m.params[1],m.params[2]
        source_server=(m.prefix or self.uplink_sid or "001")
        if kind == "S":
            mech=(data or '').upper()
            if mech != "PLAIN":
                await self.sasl_finish(source_server,puid,False); return
            self.sasl_sessions[puid]={"server":source_server,"buf":"","started":time.time()}
            await self.sasl_send(source_server,puid,"C","+")
            return
        if kind == "D":
            self.sasl_sessions.pop(puid,None); return
        if kind != "C" or puid not in self.sasl_sessions:
            return
        if data != "+":
            self.sasl_sessions[puid]["buf"] += data
        # PLAIN normally arrives in one chunk; '+' denotes an empty/final chunk.
        payload=self.sasl_sessions[puid]["buf"]
        if not payload:
            return
        try:
            raw=base64.b64decode(payload, validate=True)
            parts=raw.split(b"\x00")
            if len(parts) != 3:
                raise ValueError("invalid PLAIN frame")
            authcid=parts[1].decode('utf-8','strict')
            passwd=parts[2].decode('utf-8','strict')
            row=self.db.authenticate(authcid,passwd)
            if row:
                logging.info("SASL success for %s", row['username'])
                await self.sasl_finish(source_server,puid,True,row['username'])
            else:
                logging.warning("SASL failed for %s", authcid)
                await self.sasl_finish(source_server,puid,False)
        except Exception as exc:
            logging.warning("SASL decode/auth error: %s", exc)
            await self.sasl_finish(source_server,puid,False)

    async def handle_privmsg(self, source, target, text):
        parts=text.strip().split()
        if not parts: return
        command=parts[0].upper()
        if target.lower()=="nickserv":
            if command=="HELP":
                await self.notice("NickServ", source, "LXBG NickServ: Registrierung und Passwortverwaltung erfolgen im Web. IRC-Login via SASL/Token folgt.")
            elif command=="INFO" and len(parts)>1:
                row=self.db.nickname_owner(parts[1]); state="registriert" if row else "nicht registriert"
                await self.notice("NickServ", source, f"{parts[1]} ist {state}.")
            else:
                await self.notice("NickServ", source, "Web-first Service. Nutze HELP oder das Webpanel.")
        elif target.lower()=="chanserv":
            if command=="HELP":
                await self.notice("ChanServ", source, "LXBG ChanServ: Channel-Registrierung und Rechte werden im Web verwaltet.")
            elif command=="INFO" and len(parts)>1:
                row=self.db.channel(parts[1]); state="registriert" if row else "nicht registriert"
                await self.notice("ChanServ", source, f"{parts[1]} ist {state}.")
            else:
                await self.notice("ChanServ", source, "Web-first Service. Nutze HELP oder das Webpanel.")

    async def handle(self, m):
        if m.command=="PROTOCTL":
            for token in m.params:
                if token.startswith("SID="):
                    self.uplink_sid=token.split("=",1)[1]
            return
        if m.command=="PING" and m.params:
            await self.send("PONG :"+m.params[-1]); return
        if m.command=="UID" and len(m.params)>=6:
            nick,uid=m.params[0],m.params[5]
            self.users[uid]={"nick":nick}; self.nick_to_uid[nick.lower()]=uid
            return
        if m.command=="NICK" and m.prefix and m.params:
            uid=m.prefix if m.prefix in self.users else self.nick_to_uid.get(m.prefix.lower())
            if uid:
                self.nick_to_uid.pop(self.users[uid]["nick"].lower(),None)
                self.users[uid]["nick"]=m.params[0]; self.nick_to_uid[m.params[0].lower()]=uid
            return
        if m.command in ("QUIT","KILL") and m.prefix:
            uid=m.prefix if m.prefix in self.users else self.nick_to_uid.get(m.prefix.lower())
            if uid and uid in self.users:
                self.nick_to_uid.pop(self.users[uid]["nick"].lower(),None); self.users.pop(uid,None)
            return
        if m.command=="EOS":
            if self.uplink_sid and m.prefix != self.uplink_sid:
                return
            logging.info("Network sync complete; introducing LXBG service clients")
            for nick,gecos in self.cfg.service_nicks.items():
                if nick not in self.service_uids: await self.introduce_service(nick,gecos)
            await self.send(f":{self.cfg.sid} MD client {self.cfg.sid} saslmechlist :PLAIN")
            await self.send("EOS"); return
        if m.command=="SASL":
            await self.handle_sasl(m); return
        if m.command=="PRIVMSG" and len(m.params)>=2:
            await self.handle_privmsg(m.prefix or "", m.params[0], m.params[1])

    async def run(self):
        delay=2
        while True:
            try:
                logging.info("Connecting to UnrealIRCd %s:%s as %s", self.cfg.irc_host, self.cfg.irc_port, self.cfg.server_name)
                self.reader,self.writer=await asyncio.open_connection(self.cfg.irc_host,self.cfg.irc_port)
                await self.handshake(); delay=2
                while True:
                    data=await self.reader.readline()
                    if not data: raise ConnectionError("uplink closed")
                    line=data.decode(errors="replace").rstrip("\r\n")
                    logging.debug("<- %s", line)
                    await self.handle(IRCMessage(line))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logging.exception("Uplink error: %s", exc)
                if self.writer:
                    try: self.writer.close(); await self.writer.wait_closed()
                    except Exception: pass
                await asyncio.sleep(delay); delay=min(delay*2,30)

def selftest():
    tests=[":001AAAAAA PRIVMSG NickServ :HELP","PING :123","UID Jeff 1 1 user host 001AAAAAA 0 +ix * * * :Jeff"]
    parsed=[IRCMessage(x) for x in tests]
    assert parsed[0].command=="PRIVMSG" and parsed[0].params[1]=="HELP"
    assert parsed[1].command=="PING" and parsed[1].params[0]=="123"
    assert parsed[2].command=="UID" and parsed[2].params[0]=="Jeff"
    print("LXBG Services self-test: OK")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="/etc/lxbg-services/config.json")
    ap.add_argument("--self-test",action="store_true"); ap.add_argument("--db-test",action="store_true"); ap.add_argument("--debug",action="store_true")
    args=ap.parse_args()
    if args.self_test: selftest(); return 0
    cfg=Config.load(args.config); db=Database(cfg.db)
    if args.db_test:
        info=db.ping(); print(f"DB OK: {info['db']} / {info['v']}"); return 0
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try: asyncio.run(LXBGServices(cfg,db).run())
    except KeyboardInterrupt: pass
    return 0

if __name__=="__main__": raise SystemExit(main())
