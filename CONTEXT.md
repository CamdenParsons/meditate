# Meditate

Logs focused seated sessions at a desk. Meditation and work are the same
activity here — sitting down, deliberately, to do one thing — so the app
models them as one concept and does not try to tell them apart.

## Language

**Session**:
One focused seated stretch at the desk, opened deliberately by the person
sitting down. The only unit the app records.
_Avoid_: sit, stint, meditation, work session, focus block, timer

**Presence**:
Whether the person touched the keyboard, mouse or trackpad during a given
second of a Session. Recorded as timing only — never which keys.
_Avoid_: activity, input, engagement, usage

**Stillness**:
The absence of Presence. Whether a long stretch of Stillness is good or
bad depends on what the person sat down to do, which the app does not
know, so it never says.
_Avoid_: idle, away, inactive

**Timeline**:
The shape of Presence across a whole Session, summarised into a fixed
number of columns so any Session length renders the same width.
_Avoid_: sparkline, graph, chart

**Expiry**:
The stretch of Stillness after which an unattended Session is closed on
the person's behalf, because they walked away without ending it.
_Avoid_: timeout, gap, idle limit

**Gong**:
The struck sound that marks a Session. It plays at the start, at the end,
and at intervals throughout.
_Avoid_: bell, chime, alarm, notification

**Recenter Gong**:
The shorter, quieter cut of the Gong used for the interval strikes, so a
mid-session reminder does not dominate a room the way the full one does.
_Avoid_: interval bell, break reminder, nudge

**Activity**:
What you did during a Session, gathered once when it ends and stored on
it. Read from the traces the work already leaves behind, never from
anything you have to fill in.
_Avoid_: progress, work log, history

**Provider**:
One source of Activity, answering for a single window of time - your
Claude Code sessions, your GitHub account, the commits in a repository.
Providers are asked in turn and each may read what the ones before it
found.
_Avoid_: collector, plugin, integration, source

**Pointer**:
What an Activity entry leaves you so you can answer "what was I doing" -
a title, the prompts typed, a transcript path, a commit subject. Enough
to recall the work or go read it, never a way to resume it.
_Avoid_: link, reference, resume

**Ticket**:
An issue id such as `ACME-482`, recognised inside a branch name, a commit
subject or a pull request title. A Ticket is only ever an id; the issue
it names lives in Linear, and is reported in full only when the Linear
provider can reach it.
_Avoid_: issue, story, card

**Device**:
The machine a Session was recorded on. Stamped on every Session so logs
from several machines can be read together.
_Avoid_: machine, host, computer
