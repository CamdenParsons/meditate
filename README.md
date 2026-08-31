# meditate

A focus timer for the terminal. It keeps track of what you actually got
done in each session.

You start it when you sit down to work. It counts down. Every so often it
plays a gong so you notice the time. When the session ends it writes one
line to a plain text file: how long you sat, how much of that time you
were at the keyboard, and what came out of it.

That file is easy to read back later, either by you or by whatever program
you point at it.

```
                       \\       |             |       //
                         \       |           |       /
                          \                         /
                   \                                       /
                    \\                  _                //
           --                      _ooOoo_                        --
            ---                   o8888888o                     ---
               --                 88" . "88                   --
                                  (| -_- |)
                                  O\  =  /O
          -----                ____/`---'\____                  -----
                             .'  \\|     |//  `.
                            /  \\|||  :  |||//  \
                           /  _||||| -:- |||||_  \
         -----             |   | \\\  -  /'| |   |               -----
                           | \_|  `\`---'//  |_/ |
                           \  .-\__ `-. -'__/-.  /
           ----          ___`. .'  /--.--\  `. .'___            ----
                      ."" '<  `.___\_<|>_/___.' _> \"".
                     | | :  `- \`. ;`. _/; .'/ /  .' ; |
               --    \  \ `-.   \_\_`. _.'_/_/  -' _.' /      --
            ---       `-.`___`-.__\ \___  /__.-'_.'_.-'         ---
           --                      `=--=-'                        --
                    //                                   \\
                   /                                       \
                          /                         \
                         /       |           |       \
                       //       |             |       \\
                             █▀█ ▀▀█     █ █ █▀▀
                             █ █   █  ▀  ▀▀█ ▀▀█
                             ▀▀▀   ▀  ▀    ▀ ▀▀▀
                ──────────────────────────────────────────────
                              next gong in 00:15
                               still for 00:01
                           [space] pause   [q] end
```

Most timers only measure the time. They cannot tell whether you were
actually there. This one measures both.

For the first part, it checks once a second whether you touched the
keyboard or trackpad. It never records which keys. macOS only tells it how
long since the last input, so there is nothing to capture and no
permission to ask for.

For the second part, when a session ends it asks your tools what they
recorded during it: git commits, pull requests, and if you use them,
Claude Code sessions and Linear issues.

```
$ meditate log
  2026-08-30 09:12    2:28:00  ▅▆▇▇█▆▅▄▄▃▂▁▆▇▇▇▇██▆▅▄▃▂▂▁  ▁▁▂▂▃▄  57%  ACME-482  webhook retry backoff
  2026-08-30 14:02  ~   32:00  ▁                               ▁     2%

  2 sessions over 1 day, 3:00:00 total.
```

The bars show the shape of the session. The percentage is how much of it
had input. A `~` means you walked away and it expired, so it was recorded
as ending at your last keystroke instead of hours later.

**macOS only.** Sound goes through `afplay`, and the input check reads
`HIDIdleTime` from `ioreg`. Nothing else is needed. Python 3 standard
library, no dependencies, no install step.

The app is called *meditate* because that is what it was built for first.
The next section explains how it changed.

## Where it came from

It started as a meditation timer. I wanted a real gong for sitting at my
desk, and nothing else.

The tracking came second, for an unflattering reason. I wanted to know
whether I was cheating. It is easy to sit down for twenty minutes and
spend six of them answering a message. So it started checking, once a
second, whether I had touched the keyboard, and drawing the result as a
line.

Then I noticed I was starting it before work too. The shape is the same:
sit down, do one thing, stop when the bell rings. It replaced my pomodoro
timer. I am aware that building your own focus timer is itself a way of
avoiding work.

The cheating check turned out to be the more useful part. The same line
that catches you fidgeting through a meditation shows, over weeks, how
productive you were and how steady your flow is. Once every focused block
was going through it, the next question was what those blocks produced, so
it started recording that too.

It works alongside an agent skill I run, which keeps my issue tracker up
to date while I work instead of at the end of the day. The two halves fit
together. The skill records what the work was. This records when I was
actually doing it, and for how long. The log is one JSON object per line
so that a program can read it as easily as I can.

That history is why there is one kind of session and no work or meditation
setting, and why the app shows your stillness but never judges it. In a
meditation, input means you were distracted. In deep work, it means you
were engaged. The same number means opposite things, and only you know
which one you sat down for.

## Quick start

```
git clone https://github.com/CamdenParsons/meditate
cd meditate
./meditate 20 -i 5                              # 20 minutes, gong every 5
ln -s "$PWD/meditate" /usr/local/bin/meditate   # optional, run it anywhere
```

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

## How a session ends

| ending     | when                                              |
|------------|---------------------------------------------------|
| `you`      | you pressed `q`, or ctrl-c                         |
| `duration` | you asked for a fixed length and it elapsed        |
| `expired`  | you stopped touching the machine for the expiry    |

An expired session is recorded as ending at your **last input**, not when
the expiry fired. Otherwise walking off at 10am and noticing at 6pm would
log eight hours. See [ADR 0003](docs/adr/0003-expiry-ends-at-last-input.md).

## What gets recorded

Once a second it records whether there was input, and when. It never
records which keys. That is why it needs no permission and captures no
content
([ADR 0001](docs/adr/0001-presence-is-timing-only.md)).

The app will not tell you whether your stillness was good. That depends on
what you sat down to do, and it does not know.

Sessions live in `~/.meditate/sessions.jsonl`, one JSON object per line,
each stamped with the device name so several machines can be merged later.

## What you did

When a Session ends, the app looks up what you actually did during it and
stores it on the session row. Nothing to fill in - it reads the traces
your work already leaves.

```
meditate show          what you did in the last session
meditate show -n 2     the one before that
```

```
  ACME-482 [In Progress]  Retry the webhook dispatcher on 5xx
  ACME-491
  PR opened acme/api#218  Retry the webhook dispatcher (ACME-482)
  push   acme/api  acme-482-webhook-retries
  a31b142 api  Back off exponentially instead of fixed 5s
  claude  412 msgs  api  webhook retry backoff
           · the dispatcher gives up after one 502, lets fix that
           · does the backoff need to be jittered
           ~/.claude/projects/-Users-you-src-api/778b6a01-....jsonl
```

The point of a Claude entry is answering "what was I doing", so it carries
what you need to answer that without opening anything: the title Claude
Code gave the session, the prompts you typed inside the window, and the
transcript path when you want to read or grep the whole thing. The busiest
session's title also shows on the `log` row.

Three providers ship, and each is best-effort - one that fails or finds
nothing is skipped, and the Session is still recorded:

| provider  | what it answers                                   | needs        |
|-----------|---------------------------------------------------|--------------|
| `claude`  | Claude Code sessions active in the window         | nothing      |
| `github`  | pushes, PRs, reviews, comments, branches          | `gh` logged in |
| `commits` | local commits, including unpushed ones            | nothing      |
| `linear`  | issues you updated, with title and status         | `LINEAR_API_KEY` |
| `tickets` | ids mentioned in branches, commits and PR titles  | nothing      |

### Why `linear` needs a key

Issue work leaves no trace anywhere else. Moving four issues to Cancelled
in the Linear UI touches no branch, no commit and no pull request, so the
`tickets` provider - which reads ids off the work - cannot see it at all.
Only Linear knows.

Create a personal API key in Linear under **Settings > Security & access >
Personal API keys**, then put it in a `.env`:

```
mkdir -p ~/.meditate && cp .env.example ~/.meditate/.env
$EDITOR ~/.meditate/.env          # LINEAR_API_KEY=lin_api_...
```

Without it the provider returns nothing and everything else carries on.
Ids it reports in full are dropped from the bare `tickets` list, so an
issue appears once, with its title and status.

### What "attributed to a session" means

Attribution is by **time window**, not causality: whatever your accounts
did between the Session opening and its recorded end is what gets stored.
Usually that is exactly the work you sat down to do. It is not always:

- a scheduled job pushing under your account counts as yours
- work written yesterday but pushed during the sitting counts, because
  pushes are stamped when they happen, not when the code was written
- a Claude session already running when you sat down contributes only its
  messages inside the window, and is labelled `(continued)`

So it tells you what happened while you sat, which is not always the same
as what the sitting caused.

The Claude transcripts carry a `cwd`, so the sessions you had also say
which repositories to search for commits - no configuration.

GitHub comes from the user events feed rather than the contributions API,
because the latter reports zero for private repositories
([ADR 0004](docs/adr/0004-github-events-not-contributions.md)). Linear ids
are read out of branch names and PR titles rather than fetched, so no API
key is needed ([ADR 0005](docs/adr/0005-tickets-are-scraped-not-fetched.md)).

Settings come from `~/.meditate/.env`, or a `.env` beside the script. See
[`.env.example`](.env.example). Anything already set in your shell wins, so
`MEDITATE_DEBUG=1 meditate 20` works without editing the file.

| variable            | effect                                            |
|---------------------|---------------------------------------------------|
| `LINEAR_API_KEY`    | enables the `linear` provider                     |
| `MEDITATE_ACTIVITY` | comma-separated provider names, the rest are skipped |
| `MEDITATE_REPOS`    | extra repositories for the `commits` provider     |
| `MEDITATE_DEBUG`    | print provider failures instead of swallowing them |
| `--no-progress`     | skip the lookup for one session                   |

Providers are silent on failure so a broken one cannot fail a Session.
That silence once hid a real bug for a release, which is why
`MEDITATE_DEBUG` exists. Reach for it first when a provider returns
nothing you expected.

Adding a source means adding a module with a `name` and a
`collect(window, found)`, then listing it in
`medcore/activity/__init__.py`.

## The gong

`sounds/bell.m4a` is a 32-inch Paiste gong, single strike, CC0, from
Freesound via Openverse. It has been trimmed to the strike, pitched down
4 semitones by tape-style slow-down (which deepens it and stretches the
decay), placed in a synthesized cathedral convolution reverb, and widened
mid/side with everything below 120 Hz kept mono so the weight stays
centred. It runs 41 seconds.

`sounds/recenter.m4a` is a shorter, 10 dB quieter cut of the same gong,
used for the interval strikes so a mid-session reminder does not take
over the room.

Lengths are read from the files, so dropping your own gong in just works.
Both files derive from a single CC0 recording.

## The art

A haloed seated Buddha sits above the clock. The figure is by **hjw**
(Hayley Jane Wakenshaw), from https://asciiart.website/art/3832. The
original's ground line and `hjw` signature have been trimmed so the
figure floats inside its halo. Credit stays here and in `art/README.md`.
The halo is generated by `scripts/make_rays.py`, a build-time script that
writes `art/buddha.txt` from `art/figure.txt`. Re-run it to retune.

The screen degrades rather than clipping: the haloed figure on a large
terminal, the plain figure on a medium one, and nothing on a small one.
Point `MEDITATE_ART` at any `.txt` file to use your own instead.

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
arguments, so the ending rules and the hour-long expiry are tested in
milliseconds. Run them with `python3 tests/test_session.py`.

## Not yet

Multi-device support. Sessions already carry a device name so the logs
can be merged without a migration, but nothing merges them today.
