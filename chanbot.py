#!/usr/bin/env python
import os
from ircbot import SingleServerIRCBot
from irclib import irc_lower
import commands

class ChanBot(SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.commandsmt = os.path.getmtime(commands.__file__)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        commands.schedule_update_subs(self, hour=9, minute=0)

    def on_privmsg(self, c, e):
        msg = e.arguments()[0]
        msg = msg.strip()
        self.do_command(e, msg)

    def on_pubmsg(self, c, e):
        n, c, msg = e.arguments()[0].partition(":")
        msg = msg.strip()
        if msg and irc_lower(n) == irc_lower(self.connection.get_nickname()):
            self.do_command(e, msg)

    def do_command(self, e, msg):
        cmd, s, args = msg.partition(' ')
        cmd = cmd.lower()

        if not cmd:
            return

        try:
            mt = os.path.getmtime(commands.__file__)
        except Exception, e:
            print 'Exception %s checking command module' % repr(e)
            return

        if mt != self.commandsmt:
            try:
                reload(commands)
            except Exception, e:
                print 'Exception %s reloading command module' % repr(e)
                return
            self.commandsmt = mt

        try:
            commands.handle_command(self, e, cmd, args)
        except Exception, e:
            print 'Exception %s handling command' % repr(e)


if __name__ == "__main__":
    bot = ChanBot(
        channel  = '#london-hack-space-dev',
        nickname = 'hackbot',
        server   = 'irc.freenode.org',
    )
    bot.start()

