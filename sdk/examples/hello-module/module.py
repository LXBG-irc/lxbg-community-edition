"""LXBG Module SDK 0.1 example.

Runtime binding is intentionally not implemented in Community Edition 1.0 yet.
"""

def on_channel_join(event, lxbg):
    lxbg.irc.message(event["channel"], f'Welcome {event["nick"]}!')
