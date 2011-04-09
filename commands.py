import chanbot
import time
from datetime import datetime, timedelta
from urllib import urlopen
from irclib import nm_to_n 

STATS_URL = 'http://london.hackspace.org.uk/members/member_stats.php'
OPS_CHAN = '#london-hack-space'
CHANSERV = 'chanserv'
CHANSERV = '#london-hack-space-dev'
TRUSTED_NICK = 'ms7821'

# Wrap callbacks so we use the latest code

def callback(f):
    def wrapped(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception, e:
            print 'Exception %s during callback' % repr(e)
    return wrapped

@callback
def update_subs(*args, **kwargs):
    _update_subs(*args, **kwargs)

@callback
def schedule_update_subs(*args, **kwargs):
    _schedule_update_subs(*args, **kwargs)

@callback
def handle_command(*args, **kwargs):
    _handle_command(*args, **kwargs)

def _handle_command(bot, e, cmd, args):

    c = bot.connection
    nick = nm_to_n(e.source())

    if cmd in ['die', 'quit', 'foad']:
        bot.die(msg='Quit requested by %s' % nick)

    elif cmd == 'ping':
        if e.target().startswith('#'):
            t = e.target()
        else:
            t = nick

        c.privmsg(t, 'Pong!')

    elif cmd == 'subs' and nick == TRUSTED_NICK:
        at = time.strptime(args, '%H:%M')
        _schedule_update_subs(bot, at.tm_hour, at.tm_min)

    elif cmd == 'op' and nick == TRUSTED_NICK:
        for i in args.split(' '):
            c.privmsg(CHANSERV, 'access %s add %s member' % (OPS_CHAN, args))
            c.privmsg(CHANSERV, 'op %s %s' % (OPS_CHAN, args))

    elif cmd == 'deop' and nick == TRUSTED_NICK:
        for i in args.split(' '):
            c.privmsg(CHANSERV, 'access %s del %s' % (OPS_CHAN, args))
            c.privmsg(CHANSERV, 'deop %s %s' % (OPS_CHAN, args))

    else:
        c.notice(nick, "I didn't understand \"%s\"" % cmd)

def _schedule_update_subs(bot, hour, minute):
    now = datetime.now()
    at = now.replace(hour=hour, minute=minute, second=0)
    if at <= now:
        at += timedelta(days=1)
    at = time.mktime(at.timetuple())

    c = bot.connection
    c.execute_at(at, update_subs, [bot])
    c.execute_at(at, schedule_update_subs, [bot, hour, minute])

def _update_subs(bot):
    f = urlopen(STATS_URL)
    stats = dict(s.split(':') for s in f.read().split(' '))

    c = bot.connection
    c.notice(bot.channel, stats)

