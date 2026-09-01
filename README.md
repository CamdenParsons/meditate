# meditate

A pomodoro-style timer you start from your terminal, that automatically
tracks your activity and organises it by session. Use it for a personal
meditation session, or for your flow and productivity at work.

It counts down and rings a gong at intervals, and when the session ends it
asks your tools what happened while you were sitting there and writes the
answer down. Commits, pull requests, issues and Claude Code sessions from
that window, along with how long you sat and how much of that time you
spent typing. Nothing is filled in by hand.


![the timer running](docs/screenshots/timer.png)

## Where it came from

It started as a meditation timer. I wanted a real gong and nothing else.

The tracking came second, for a slightly embarrassing reason: I wanted to
know whether I was cheating. It is easy to sit down for twenty minutes and
spend six of them answering a message, so it started checking once a second
whether I had touched anything, and drawing the result as a line.

Then I started using it for focus blocks at work, because the shape is the
same. You sit down, do one thing, and stop when the bell rings. It replaced
my pomodoro timer, though I am aware that building your own focus timer is
itself a way of avoiding work.

I kept the gong because marking the intervals by ear works about as well at
a desk as it does on a cushion, and it tells me where I am in the session
without looking up.

The tracking turned out to be the more useful half. The same line that
shows whether I stayed still during a meditation also shows, across a few
weeks, how much of my focus time was real. Once every block was going
through it the obvious next question was what those blocks produced, so it
started recording that as well.

It works alongside an agent skill that keeps my issue tracker current while
I work rather than in a scramble before the sync meeting. The skill records
what the work was, and this records when I was actually doing it and for
how long. The log is one JSON object per line, so a program can read it
about as easily as I can.

That history is probably why there is one kind of session and no work or
meditation setting, and why the app reports your activity without grading
it. During a sit, activity means you were distracted. During focus time it
means you were working. The same number means opposite things, and only you
know which one you sat down for.

## Quick start

```
git clone https://github.com/CamdenParsons/meditate
cd meditate
./meditate 20 -i 5                              # 20 minutes, gong every 5
ln -s "$PWD/meditate" /usr/local/bin/meditate   # optional, run it anywhere
```

macOS only. Sound goes through `afplay` and the input check reads
`HIDIdleTime` from `ioreg`, both of which are macOS. Nothing else is
needed: Python 3 standard library, no dependencies, no install step.

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

`space` pauses and `q` ends. Start one in a background terminal when you
sit down and then forget about it.

A session ends one of three ways. You stop it, a fixed length runs out, or
you stop touching the machine long enough to trip the expiry. An expired
session is recorded as ending at your last input, so walking off at 10am
and noticing at 6pm does not log you eight hours.

## Review your session log

Every session appends one line to `~/.meditate/sessions.jsonl`.

![meditate log](docs/screenshots/log.png)


The bars are the shape of the session, followed by metrics about how the time was spent.


See one session with `meditate show`

![meditate show](docs/screenshots/show.png)



## Activity providers

When a session ends each provider is asked what it saw during that window.
They are all best-effort, and one that fails or finds nothing is skipped
while the session is still recorded.

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



## Common use cases

`meditate 20 -i 5` is a sit, twenty minutes long with a gong every five.
The goal is to touch nothing, and the percentage afterwards tells you
whether you managed it.

`meditate 25 -i 0` is a pomodoro block with nothing interrupting it, and
`meditate show` afterwards tells you what came out of it.

`meditate` on its own runs until you stop it, gonging every half hour. If
you get pulled away and forget it is running it expires after an hour and
keeps only the time you were actually there.

`meditate log` is the week at a glance: every session, how present you were
in each, and what each one touched.

`meditate show -n 3` opens the third session back, for when you are trying
to remember what you were doing on Tuesday.
