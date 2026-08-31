# An expired Session is recorded as ending at its last input

People forget to close Sessions, so one expires after a stretch of
Stillness. Recording the end at the moment expiry *fired* would log the
whole walk-away period as time at the desk — leave at 10am with a
one-hour Expiry and the log claims an extra hour. The end is therefore
backdated to the last observed Presence, and the trailing Stillness is
trimmed from the Timeline too.

## Consequences

A genuinely motionless Session — a long meditation with no input at all —
is indistinguishable from walking away, and gets truncated to near zero.
Fixed-length Sessions exist for exactly that case and are exempt, since
their end is known in advance.
