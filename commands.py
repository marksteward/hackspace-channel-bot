import chanbot
import time
from datetime import datetime, timedelta
from urllib import urlopen
from decorator import decorator
from irclib import nm_to_n, is_channel

STATS_URL = 'http://london.hackspace.org.uk/members/member_stats.php'
OPS_CHAN = '#london-hack-space'
#CHANSERV = 'chanserv'
CHANSERV = '#london-hack-space-dev'
TRUSTED_NICK = 'ms7821'

# Wrap callbacks so we use the latest code

@decorator
def callback(f, *args, **kwargs):
    try:
        f(*args, **kwargs)
    except Exception, e:
        print 'Exception %s during callback' % repr(e)

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
    if is_channel(e.target()):
        target = e.target()
    else:
        target = nick

    if cmd in ['die', 'quit', 'foad']:
        bot.die(msg='Quit requested by %s' % nick)

    elif cmd == 'ping':
        c.privmsg(target, 'Pong!')

    elif cmd == 'sched':
        for t, f, a in c.irclibobj.delayed_commands:
            def argstr(a):
                if repr(a) == repr(bot):
                    return 'bot'
                return repr(a)

            c.privmsg(target, '%s %s(%s)' % (
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)),
                f.__name__,
                ', '.join(map(argstr, a))
            ))

    elif cmd == 'clearsched' and nick == TRUSTED_NICK:
        c.irclibobj.delayed_commands = []
        c.privmsg(target, 'Schedule cleared')

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
        c.notice(target, "I didn't understand \"%s\"" % cmd)

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

