# Ticket ids are read off the work, not fetched from Linear

Linear's API would give issue titles and status, at the cost of a key to
create, store and rotate before the feature works at all. Every id worth
recording already appears in a branch name, a commit subject or a pull
request title, so the tickets provider reads them from what the other
providers found. No key, no configuration, no extra network call.

## Consequences

An id is all that is recorded - no title, no status - and an issue worked
on without its id appearing anywhere is missed. Ids are matched
case-insensitively, since they are upper-case in pull request titles and
lower-case in branch names, and a short denylist keeps `gpt-4` and
`sha-256` from being read as tickets. Swapping in a real Linear provider
later means adding a module, not changing anything else.
