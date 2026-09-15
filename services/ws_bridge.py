#!/usr/bin/python3
import asyncio, websockets, os
async def handler(ws,path):
 r,w=await asyncio.open_connection(os.getenv('LXBG_IRC_HOST','127.0.0.1'),int(os.getenv('LXBG_IRC_PORT','16667')))
 async def irc_to_ws():
  try:
   while True:
    line=await r.readline()
    if not line: break
    await ws.send(line.decode(errors='replace').rstrip('\r\n'))
  finally: await ws.close()
 async def ws_to_irc():
  try:
   async for msg in ws:
    if isinstance(msg,bytes): msg=msg.decode(errors='replace')
    if len(msg)>510: continue
    w.write((msg.rstrip('\r\n')+'\r\n').encode()); await w.drain()
  finally:
   w.close(); await w.wait_closed()
 await asyncio.gather(irc_to_ws(),ws_to_irc(),return_exceptions=True)
async def main():
 async with websockets.serve(handler,os.getenv('LXBG_WS_HOST','127.0.0.1'),int(os.getenv('LXBG_WS_PORT','18000')),max_size=2048,ping_interval=30,ping_timeout=30): await asyncio.Future()
asyncio.run(main())
