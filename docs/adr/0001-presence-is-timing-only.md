# Presence is recorded as timing only, never key identities

Knowing *whether* someone typed answers everything the log needs — were
they still, and was it steady — while knowing *what* they typed would
make this a keylogger, require macOS Input Monitoring permission, and put
passwords in a plaintext file. We read `HIDIdleTime`, which exposes only
how long since the last input event and is therefore incapable of
capturing content, rather than installing a `CGEventTap`.

## Consequences

Presence is whole-machine, so a colleague on the keyboard reads as the
person sitting there, and phone use during a Session reads as perfect
Stillness. Both are acceptable: the log is a personal record, not
evidence.
