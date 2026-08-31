# Meditation and desk work are one Session concept, not two

An earlier design split these into a deliberate meditation sit and an
auto-detected desk session, on the theory that Presence means distraction
in one and engagement in the other. That was wrong: both are a person
deliberately sitting down to focus, both are opened by hand, and the
split forced a nested-session problem where meditating at the desk would
be double-counted by two overlapping rows.

## Consequences

There is no `kind` field, no background watcher, and no auto-detection —
a Session exists because someone started one. The app therefore never
interprets Presence for you; it reports the percentage and the Timeline
and leaves the reading to the person who knows what they sat down to do.
