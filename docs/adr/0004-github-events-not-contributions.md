# GitHub Activity comes from the events feed, not the contributions API

The obvious source for "what did I do on GitHub" is
`contributionsCollection`, and it is the wrong one: queried for a window
in which a pull request had definitely been opened against a private
repository, it returned zero on every counter, because private
contributions are excluded unless the profile opts in. The user events
feed returned the same period in full - a hundred events, every one of
them from a private repository.

## Consequences

The feed keeps only about the last 300 events, so this reports on a
Session that just ended and cannot backfill history. Private repositories
also omit the commit list from push events - only the branch ref survives
- which is why the git provider reads commit subjects locally rather than
taking them from the feed.
