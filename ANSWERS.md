# Answers

Fill this in as you go. It is checked, and it is where the actual understanding shows.

## Task 4 — why `down_revision` and not the filename

Alembic orders revisions by `down_revision`, not by filename. The filenames are timestamped, so sorting
them would usually give the same order. Describe a situation on a team of four where it would not.

## Task 7 — the permit that never came back

Your `finally` gives the permit back. Now the machine loses power, or the process is `SIGKILL`ed:
`finally` does not run, `in_use` is stuck, and eventually nothing ever ingests again.

Describe one way to make a permit recover on its own. What would it have to know that `job_slots` does
not currently record?

## Task 8 — one database, two DSNs

| DSN | who uses it | why it cannot be the other one |
|---|---|---|
| `postgresql://meridian:meridian@localhost:55432/meridian_trips` | | |
| | | |
