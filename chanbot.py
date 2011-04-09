#! /usr/bin/env python
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
from urllib import urlopen
import time
from datetime import datetime, timedelta

STATS_URL = 'http://london.hackspace.org.uk/members/member_stats.php'
OPS_CHAN = '#london-hack-space'

class ChanBot(SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        self.schedule_update_subs(hour=9, minute=0)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments()[0])

    def on_pubmsg(self, c, e):
        n, c, msg = e.arguments()[0].partition(":")
        msg = msg.strip()
        if msg and irc_lower(n) == irc_lower(self.connection.get_nickname()):
            self.do_command(e, msg)
        return

    def do_command(self, e, msg):
        nick = nm_to_n(e.source())
        c = self.connection
        cmd, s, args = msg.partition(' ')
        cmd = cmd.lower()

        if cmd in ['die', 'quit', 'foad']:
            self.die(msg='Quit requested by %s' % nick)

        elif cmd == 'subs' and nick == 'ms7821':
            try:
                at = time.strptime(args, '%H:%M')
                self.schedule_update_subs(at.tm_hour, at.tm_min)

            except Exception, e:
                print repr(e)
                c.notice(nick, 'Exception %s parsing %s' % (repr(e), args))

        elif cmd == 'op' and nick == 'ms7821':
            for i in args.split(' '):
                c.notice(nick, 'access %s add %s +voOtsriA' % (OPS_CHAN, args))
                c.notice(nick, 'op %s %s' % (OPS_CHAN, args))

        elif cmd == 'deop' and nick == 'ms7821':
            for i in args.split(' '):
                c.notice(nick, 'access %s del %s' % (OPS_CHAN, args))
                c.notice(nick, 'deop %s %s' % (OPS_CHAN, args))


        else:
            c.notice(nick, "Not understood: " + cmd)

    def schedule_update_subs(self, hour, minute):
        now = datetime.now()
        at = now.replace(hour=hour, minute=minute, second=0)
        if at <= now:
            at += timedelta(days=1)
        at = time.mktime(at.timetuple())
        c.execute_at(at, self.update_subs, [])
        c.execute_at(at, self.schedule_update_subs, [hour, minute])

    def update_subs(self):
        try:
            f = urlopen(STATS_URL)
            stats = dict(s.split(':') for s in f.read().split(' '))
            self.connection.notice(self.channel, stats)
        except Exception, e:
            print repr(e)

if __name__ == "__main__":
    bot = ChanBot(
        channel  = '#london-hack-space-dev',
        nickname = 'hackbot',
        server   = 'irc.freenode.org',
    )
    bot.start()

