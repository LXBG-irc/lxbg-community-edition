#!/usr/bin/python3
import asyncio,json,os
from daemon import Config,Database
from argon2 import PasswordHasher
SOCK=os.getenv('LXBG_AUTH_SOCKET','/run/lxbg-services/auth.sock'); ph=PasswordHasher()
def live_auth(db,ident,pw):
 with db.connect() as cn,cn.cursor() as q:
  q.execute("SELECT id,username,anope_account,password_hash,status FROM lxbg_users WHERE status='active' AND (username_normalized=%s OR LOWER(COALESCE(anope_account,''))=%s) LIMIT 1",(ident.lower(),ident.lower()));r=q.fetchone()
  if not r:return None
  try: ph.verify(r['password_hash'],pw);return {'id':'live:'+str(r['id']),'username':r.get('anope_account') or r['username']}
  except Exception:return None
def live_token(db,ident,pw):
 if not pw.startswith('LXBG-TOKEN:'):return None
 raw=pw[11:]
 with db.connect() as cn,cn.cursor() as q:
  q.execute("SELECT t.id,t.user_id,t.token_hash,u.username,u.anope_account FROM lxbg_irc_tokens t JOIN lxbg_users u ON u.id=t.user_id WHERE t.used_at IS NULL AND t.expires_at>NOW() AND (LOWER(u.username)=LOWER(%s) OR LOWER(COALESCE(u.anope_account,''))=LOWER(%s)) ORDER BY t.id DESC LIMIT 4",(ident,ident));rows=q.fetchall()
  for r in rows:
   try:
    ph.verify(r['token_hash'],raw);q.execute("UPDATE lxbg_irc_tokens SET used_at=NOW() WHERE id=%s AND used_at IS NULL",(r['id'],));return {'id':'live:'+str(r['user_id']),'username':r.get('anope_account') or r['username']}
   except Exception:pass
 return None
def channel_lookup(db,name):
 with db.connect() as cn,cn.cursor() as q:
  q.execute("SELECT id,channel_name,created_by_user_id,founder_account,topic,modes FROM lxbg_channels WHERE LOWER(channel_name)=%s AND is_active=1 AND delete_pending=0 LIMIT 1",(name.lower(),));c=q.fetchone()
  if c:
   founder_id=''
   if c.get('created_by_user_id'):founder_id='live:'+str(c['created_by_user_id'])
   elif c.get('founder_account'):
    q.execute("SELECT id FROM lxbg_users WHERE LOWER(username)=LOWER(%s) OR LOWER(COALESCE(anope_account,''))=LOWER(%s) LIMIT 1",(c['founder_account'],c['founder_account']));u=q.fetchone();founder_id='live:'+str(u['id']) if u else ''
   q.execute("SELECT user_id,role FROM lxbg_channel_members WHERE channel_id=%s",(c['id'],));levels={};rm={'admin':75,'operator':50,'voice':30}
   for a in q.fetchall():
    if a['role'] in rm:levels['id:live:'+str(a['user_id'])]=rm[a['role']]
   if founder_id:levels['id:'+founder_id]=100
   return {'ok':True,'name':c['channel_name'],'founder_id':founder_id,'topic':c.get('topic') or '','modes':c.get('modes') or '+nt','levels':levels}
  q.execute("SELECT id,channel_name,founder_user_id,topic,modes FROM ls_channels WHERE channel_name_normalized=%s AND is_active=1 LIMIT 1",(name.lower(),));c=q.fetchone()
  if not c:return {'ok':False}
  q.execute("SELECT user_id,access_role FROM ls_channel_access WHERE channel_id=%s",(c['id'],));rm={'founder':100,'admin':75,'op':50,'halfop':50,'voice':30};levels={'id:'+str(a['user_id']):rm[a['access_role']] for a in q.fetchall() if a['access_role'] in rm}
  return {'ok':True,'name':c['channel_name'],'founder_id':str(c['founder_user_id']),'topic':c.get('topic') or '','modes':c.get('modes') or '+nt','levels':levels}
async def handle(r,w):
 try:
  req=json.loads((await asyncio.wait_for(r.readline(),3)).decode());db=Database(cfg.db)
  if req.get('op')=='channel':out=channel_lookup(db,str(req.get('channel',''))[:64])
  elif req.get('op')=='nick_owner':
   nick=str(req.get('nick',''))[:30].lower();out={'ok':True,'account_id':''}
   with db.connect() as cn,cn.cursor() as q:
    q.execute("SELECT id FROM lxbg_users WHERE status='active' AND (username_normalized=%s OR LOWER(COALESCE(anope_account,''))=%s) LIMIT 1",(nick,nick));u=q.fetchone()
    if u: out={'ok':True,'account_id':'live:'+str(u['id'])}
  elif req.get('op')=='account_meta':
   aid=str(req.get('account_id',''))[:64];out={'ok':False,'oper':False}
   if aid.startswith('live:') and aid[5:].isdigit():
    with db.connect() as cn,cn.cursor() as q:
     q.execute("SELECT role,status FROM lxbg_users WHERE id=%s LIMIT 1",(int(aid[5:]),));u=q.fetchone()
     if u: out={'ok':True,'oper':u.get('status')=='active' and str(u.get('role') or '').lower() in ('admin','owner','superadmin')}
  elif req.get('op')=='channel_update':
   name=str(req.get('channel',''))[:64].lower();topic=str(req.get('topic',''))[:512];modes=str(req.get('modes',''))[:32]
   with db.connect() as cn,cn.cursor() as q:q.execute("UPDATE lxbg_channels SET topic=%s,modes=%s,updated_at=NOW() WHERE LOWER(channel_name)=%s AND is_active=1",(topic,modes,name));out={'ok':q.rowcount>0}
  elif req.get('op')=='runtime_snapshot':
   with db.connect() as cn,cn.cursor() as q:
    q.execute("SELECT channel_name FROM lxbg_channels WHERE is_active=1 AND delete_pending=0 ORDER BY sort_order,id");chs=[x['channel_name'] for x in q.fetchall()]
   out={'ok':True,'channels':chs}
  else:
   ident=str(req.get('account',''))[:128];pw=str(req.get('password',''))[:512]
   row=live_token(db,ident,pw) if pw.startswith('LXBG-TOKEN:') else live_auth(db,ident,pw)
   if not row:row=db.authenticate(ident,pw)
   out={'ok':bool(row)}
   if row:out.update(account=row['username'],account_id=str(row['id']))
 except Exception:out={'ok':False}
 w.write((json.dumps(out)+'\n').encode());await w.drain();w.close();await w.wait_closed()
async def main():
 try:os.unlink(SOCK)
 except FileNotFoundError:pass
 srv=await asyncio.start_unix_server(handle,SOCK);os.chmod(SOCK,0o660)
 async with srv:await srv.serve_forever()
def tenant_db_cfg():
    """Use a tenant-local JKWEB database config when LXBG_TENANT_CONFIG is set.
    Falls back to the legacy services DB only for the production/legacy instance.
    """
    p=os.getenv('LXBG_TENANT_CONFIG','').strip()
    if not p:
        return None
    with open(p,'r',encoding='utf-8') as f:
        raw=json.load(f)
    d=raw.get('db') or raw.get('database') or {}
    need=('host','username','password','database')
    if not all(d.get(k) for k in need):
        raise RuntimeError('tenant database config incomplete')
    return {'host':d['host'],'port':int(d.get('port',3306)),'username':d['username'],'password':d['password'],'database':d['database']}

cfg=Config.load(os.getenv('LXBG_SERVICES_CONFIG','/etc/lxbg-services/config.json'))
tdb=tenant_db_cfg()
if tdb is not None:
    cfg.db=tdb
asyncio.run(main())
