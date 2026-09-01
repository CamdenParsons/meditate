# meditate

A pomodoro-style timer you start from your terminal, that automatically
tracks your activity and organises it by session. Use it for a personal
meditation session, or for your flow and productivity at work.

It counts down and rings a gong every so often. When the session's over it
goes and asks your tools what happened while you were sitting there, then
writes it down. Commits, pull requests, issues, Claude Code sessions. Plus
how long you sat and how much of that you actually spent typing. You don't
fill in anything.

Lots of things will time a work session. What I wanted was the record of
what came out of one.

The sound's a zen gong. I use it like tingsha in Buddhist meditation, to
mark the intervals and pull my attention back.

![the timer running](docs/screenshots/timer.png)

## Where it came from

It started as a meditation timer. I wanted a real gong and nothing else.

The tracking came second, and for a slightly embarrassing reason: I wanted
to know if I was cheating. It's very easy to sit down for twenty minutes
and spend six of them answering a message. So it started checking once a
second whether I'd touched anything, and drawing that as a line. Hard to
argue with a line.

Then I started using it for focus blocks at work, because it's the same
shape. Sit down, do one thing, stop when the bell rings. It replaced my
pomodoro timer. And yes, building your own focus timer is itself a way of
avoiding work.

I kept the gong. Marking the intervals by ear works just as well at a desk
as on a cushion, and it tells me where I am without looking up.

The tracking turned out to be the more useful half. That same line showing
whether I sat still also shows, across a few weeks, how much of my focus
time was real. And once every block was going through it, the obvious next
question was what those blocks actually produced. So it started recording
that too.

It pairs with an agent skill I run that keeps my issue tracker current
while I work, rather than in a scramble at 6pm. The skill knows what the
work was. This knows when I was actually doing it, and for how long.

That's why there's one kind of session and no work-or-meditation setting,
and why the app shows you the numbers but never grades them. During a sit,
activity means you got distracted. During focus time it means you were
working. Same number, opposite meanings, and only you know which one you
sat down for.

## Quick start

```
git clone https://github.com/CamdenParsons/meditate
cd meditate
./meditate 20 -i 5                              # 20 minutes, gong every 5
ln -s "$PWD/meditate" /usr/local/bin/meditate   # optional, run it anywhere
```

macOS only. Sound goes through `afplay`, and the input check reads
`HIDIdleTime` from `ioreg`. Nothing else is needed. Python 3 standard
library, no dependencies, no install step.

## Commands

```
meditate            start a session, gong every 30 min
meditate 20         a 20 minute session
meditate -i 5       gong every 5 min
meditate -e 30      expire after 30 min with no input
meditate log        past sessions
meditate show       what you did in the last one (-n 2 for the one before)
meditate bell       ring the gong once
```

`space` pauses, `q` ends. Start one in a background terminal when you sit
down and forget about it.

A session ends in one of three ways. You stop it, a fixed length runs out,
or you stop touching the machine for the expiry window. An expired session
is recorded as ending at your last input, not when the expiry fired.
Otherwise walking off at 10am and noticing at 6pm would log eight hours.

## The log

Every session appends one line to `~/.meditate/sessions.jsonl`.

![meditate log](docs/screenshots/log.png)

*Example data, so the shapes differ. Every number in it was produced by
the real code.*

The bars are the shape of the session. Then two numbers.

`57% in` is how much of the session had keyboard or trackpad input,
sampled once a second. Read a diff for three minutes and that counts as
inactive, so it's really hands-on-keys time, not engagement.

`91% even` is how evenly that input was spread. It describes a shape and
nothing more. High isn't better. It's blank on a session that's too short
or too still for the arithmetic to mean much.

A `~` marks one that expired because you walked away.

The second line rolls up what the session touched. For the individual
records, open one up with `meditate show`.

Once a second it records whether there was input, and when. Never which
keys. That's why it needs no permission and captures nothing.

### What the percentage can't tell you

Twenty minutes reading a diff and four minutes typing will score badly
here. A bad afternoon fighting a flaky test scores great. And if an agent
writes most of your code now, hands on the keyboard is closer to a measure
of how much correcting you're doing.

So don't read `% in` as productivity. It answers a smaller question, which
is whether you were at the machine. That's still worth knowing. It's what
lets a session expire at your last keystroke instead of logging the hour
you were at lunch, and it's the original question I built this to answer,
back when the goal was to sit still and touch nothing.

The useful half is what the session produced. That's `meditate show`.

`meditate show` opens a single session and lists everything attributed to
it:

![meditate show](docs/screenshots/show.png)

All of it comes from traces your work already leaves behind. Nothing to
fill in.

It attributes by time window, so whatever your accounts did between the
session opening and its recorded end is what gets stored.

## Activity providers

When a session ends, each provider gets asked what it saw in that window.
They're all best-effort. One that fails, or finds nothing, is skipped and
the session still gets recorded.

| provider  | what it answers                                  | needs            |
|-----------|--------------------------------------------------|------------------|
| `claude`  | Claude Code sessions active in the window        | nothing          |
| `github`  | pushes, PRs, reviews, comments, branches         | `gh` logged in   |
| `commits` | local commits, including unpushed ones           | nothing          |
| `linear`  | issues you updated, with title and status        | `LINEAR_API_KEY` |
| `tickets` | ids mentioned in branches, commits and PR titles | nothing          |

Settings live in `~/.meditate/.env`. See [`.env.example`](.env.example).

Adding a source means writing a module with a `name` and a
`collect(window, found)`, then listing it in `medcore/activity/__init__.py`.

## Layout

```
meditate          entry point
medcore/
  session.py      a Session: when it ends, what it records
  activity/       what you did: one module per source
  config.py       settings, read from .env
  presence.py     per-second presence, and its summary
  inputwatch.py   how long since the human last touched the machine
  audio.py        striking the gong
  store.py        reading and writing the log
  display.py      drawing to the terminal
  cli.py          argument parsing and the terminal loop
art/              ascii art shown above the clock
scripts/          build-time art generation
tests/            component tests, on a fake clock
```

`session.py` and `presence.py` take their clock and input source as
arguments, so the hour-long expiry rules get tested in milliseconds. Run
them with `python3 -m unittest discover -s tests`.

## Common use cases

**A meditation sit.** `meditate 20 -i 5` gives you twenty minutes with a
gong every five. The goal is to touch nothing, and the percentage
afterwards tells you if you managed it.

**A pomodoro block.** `meditate 25 -i 0` runs twenty five minutes with
nothing interrupting, then `meditate show` tells you what came out of it.

**Open-ended deep work.** `meditate` on its own runs until you stop it,
gonging every thirty minutes. If you get pulled away and forget it's
running, it expires after an hour and only records the time you were
actually there.

**Reviewing the week.** `meditate log` shows every session, how present
you were in each, and which tickets they touched.

**Answering "what was I doing".** `meditate show -n 3` opens the third
session back and lists the commits, pull requests and Claude sessions from
that window.
