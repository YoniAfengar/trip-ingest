# Ingest Pipeline

_The ingest you can rerun at 3am._

Meridian Bikes runs a city bike-share. Every night a vendor drops a file of the day's trips into a
directory — `2026-03-14.jsonl`, one JSON object per line — and something has to get those trips into
Postgres before the morning dashboards run.

That something is currently a 200-line script that nobody will touch. You are replacing it.

Four sentences from the person who carries the pager. They are the whole specification, and every task
below exists to satisfy one of them:

1. *"Some nights the drop is bigger than the machine's memory."*
2. *"When the job dies half way, I rerun it. It must not double-load."*
3. *"One bad row must not cost me the other four hundred thousand — but I need to see the bad rows in
   the morning."*
4. *"Two of these may run at once. Never three: the third one takes the database down."*

**Budget** ~3h25, including §0. You need `git`, `docker`, `uv`, and Python 3.11+ on your own machine.

---

## 0. Your repository (~10 min)

This exercise leaves the course. Copy it somewhere on your own machine — **not** into the course repo,
and **not** into the devcontainer. It is a new project, and you are going to run Docker on your own
laptop, the way you would at work.

```bash
cp -R hands-on/practicum/trip-ingest ~/projects/trip-ingest
cd ~/projects/trip-ingest
git init && git add -A && git commit -m "Start from the provided stub"
```

Commit the stub **before you write a line**. Then create an empty repository on GitHub, and:

```bash
git remote add origin git@github.com:<you>/trip-ingest.git
git push -u origin main
```

Commit as you finish each task. `docker-compose.yml`, `Dockerfile`, and both Alembic revisions are part
of the source: they get committed like everything else. The drops and the rejects do not — see
`.gitignore`, and understand why before you change it.

**You hand in the repository URL**, with `uv run pytest` green, `uv run pytest -m e2e` green,
`uv run mypy src/` clean, and `ANSWERS.md` filled in.

---

## 1. Stand up the database (~20 min)

Nothing in this repo runs until Postgres does, and standing it up is your job. Write a
`docker-compose.yml` with a service called **`db`** such that this exact DSN works from your shell:

```
postgresql://meridian:meridian@localhost:55432/meridian_trips
```

Read it carefully. The port is not 5432, the user is not `postgres`, and the database is not `postgres`
either. All four are wrong on purpose: you cannot get here by copying the first compose file you find.
You will have to look up how the `postgres` image is configured, and how a container port is published
to a host port.

Give `db` a **healthcheck**, and a named volume for its data. You will need both in Task 8.

**Done when** the tests stop telling you they cannot reach Postgres:

```bash
docker compose up -d db
uv run pytest tests/test_migrations.py    # still red — there is no schema yet — but no longer
                                          # "Cannot reach Postgres at ..."
```

That distinction matters. A connection refused and a missing table are different failures, and from
here on the tests will tell you which one you have.

> `settings.py` explains why this DSN is not the one the container will use. That difference is Task 8.

---

## 2. Read a drop without reading a drop (~20 min)

`src/trip_ingest/reader.py`, `read_drop`. Yield one raw JSON object per line.

Statement 1 from the pager: the drop does not fit in memory. Whatever `read_drop` returns, the caller
must be able to walk it a line at a time, and the machine must never hold more than one line.

`tests/test_reader.py` has a file whose *third* line is not JSON. Taking the first two rows must not
raise. If it does, you read ahead.

**Done when** `uv run pytest tests/test_reader.py` is green. No database involved.

---

## 3. Name the failures (~20 min)

`src/trip_ingest/errors.py` and `reader.parse_row`.

`tests/test_errors.py` is the specification of the hierarchy, and `tests/test_parse.py` of the parsing.
Read them both before you write anything.

The shape is the decision. A caller must be able to write `except RowError` and have it mean *"this line
is bad, write it aside and keep going"* — and have that `except` **not** catch *"the job cannot run at
all"*. If one `except` swallows both, a job that never started gets reported as a job with one bad line
in it, and at 3am somebody will believe the report.

A missing `started_at` is a `BadTimestamp`, not a `MissingField`. That is not pedantry: one of them means
a row is corrupt, the other means the vendor changed their schema, and you want to be able to read the
rejects file and tell which.

**Done when** `tests/test_errors.py` and `tests/test_parse.py` are green.

---

## 4. The schema, as a migration (~25 min)

The first Alembic revision creates `trips`.

```bash
uv run alembic revision -m "create trips table"     # writes alembic/versions/<...>.py
uv run alembic upgrade head
uv run alembic downgrade -1                         # it must work backwards too
```

`alembic/env.py` explains why `--autogenerate` will hand you an empty migration: there is no ORM here, so
there is nothing to diff. You write the DDL, in SQL, by hand.

Columns: `trip_id`, `station_id`, `started_at`, `distance_m`. `tests/test_migrations.py` says what the
types must be, and demands two things you should decide *for the reason*, not because a test said so:

- `started_at` is `timestamptz`. A naive timestamp is a future outage.
- `trip_id` is the primary key. Task 5 is going to ask the database to ignore trips it already has, and
  it cannot do that unless it knows what "already has" means. **The migration and the loader are one
  change**, split across two files.

Write `downgrade()` properly. A migration you cannot undo is a migration you cannot deploy on a Friday.

**Done when** everything in `tests/test_migrations.py` is green except
`test_job_slots_is_seeded_with_two_permits`, which waits for Task 7.

**Then answer in `ANSWERS.md` (3–4 sentences):** Alembic orders revisions by `down_revision`, not by
filename. The filenames are timestamped, so sorting them would *usually* give the same order. Describe a
situation on a team of four where it would not.

---

## 5. The load (~25 min)

`src/trip_ingest/loader.py`, `load_trips`. It takes the connection and an **iterable** of trips — which
will be a generator over a file bigger than memory — and returns how many rows the database did not
already have.

Statement 2 from the pager: rerunning must not double-load. There are two ways to do that.

- Read the existing trip ids into Python and filter. This reads the table back for nothing, and it is a
  **race**: two ingests both look, both see nothing, both insert.
- Tell the database to skip what it already has, in the same statement that inserts. It holds the row
  lock; it cannot race with itself.

Take the second. Postgres has a clause for exactly this, and the primary key you created in Task 4 is
what it needs to work. After the statement runs, the cursor knows how many rows were actually inserted —
which is the number this function must return, from the only party that can know it.

One more thing: `load_trips` is handed a lazy stream. It may not call `len()` on it, index it, or walk it
twice. Batch it, and send a batch per statement rather than a statement per row.

**Done when** `tests/test_loader.py` is green — including the generator and multi-batch cases.

---

## 6. Wire it together (~25 min)

`src/trip_ingest/ingest.py`: `ingest_drop`, then `run_job`.

Statement 3 from the pager. A bad row is written to `rejects/<drop-name>.rejects.jsonl` — one JSON object
per line, carrying the original row **and** why it was rejected — and the job carries on. A good row is
loaded. At the end, `run_job` returns the totals and **logs a single structured summary line at INFO**:
how many drops, how many rows read, how many loaded, how many rejected. Somebody on call must be able to
tell what happened without opening the database.

Do not use `print`. `logging` exists so that the same line can go to a terminal now and to a log
aggregator later, without editing this file.

Note where the size gate bites. `run_job` will not fit in twenty lines while it is also opening a
connection, listing a directory, ingesting each file, and summing reports. That is the limit telling you
where the seams are — and the seams are exactly the things you would want to test alone.

**Done when** the rejects file appears with the right contents and the summary line shows up:

```bash
cp sample-drops/*.jsonl drops/
uv run python -m trip_ingest drops
```

Two of the five rows in `2026-03-15.jsonl` are bad, in two different ways. Look at the third one twice.

---

## 7. Two at a time (~30 min)

Statement 4 from the pager: two ingests may run at once, never three.

You cannot enforce that in Python. The three jobs are three processes, possibly on three machines, and
the only thing they share is the database. So the count of who is running has to live *in the database*,
and the rule has to be enforced by the database.

**What a counting semaphore is.** A lock lets one holder in. A *counting semaphore* lets `n` in: it is a
counter of permits. To start work you take a permit — if one is free, the number in use goes up by one
and you proceed; if none is free, you wait until somebody gives one back. When you finish, you give yours
back, however you finish. That is all it is: a number, an agreement to check it before starting, and an
agreement to put it back.

Ours is a table.

```
job_slots(job_name, capacity, in_use)
```

Write a **second Alembic revision** that creates it and seeds the row `('ingest', 2, 0)`. The seed belongs
in the migration, not in the application: the row describes the shape of the world — that an ingest
exists, and that two of it may run — and every environment needs it before any code runs. An application
that creates its own permits on startup has a race on startup.

Add a `CHECK` so `in_use` can never exceed `capacity`. Even if your acquire is wrong, the database will
refuse.

Then write `job_slot` in `src/trip_ingest/slots.py`: a context manager that takes a permit on the way in —
waiting, with a timeout, if none is free — and gives it back on the way out, whatever happened inside.
Finally, wrap the whole of `run_job` in it.

**Two details decide whether this works, and neither is obvious.**

**Read-then-write is a race.** If you `SELECT in_use`, compare it to `capacity` in Python, and then
`UPDATE`, two jobs can both read `1`, both decide there is room, and both write `2`. The check and the
increment must be *one statement*, so that the row lock covers both:

```sql
UPDATE job_slots SET in_use = in_use + 1
 WHERE job_name = %s AND in_use < capacity
RETURNING in_use;
```

If it returns a row, you have a permit. If it returns nothing, you do not — wait, and try again.

**A permit nobody can see is not a permit.** If that `UPDATE` runs on the ingest's own connection, inside
the ingest's transaction, nobody else learns about it until the job commits — which is to say, until the
job is over, which is precisely when the count has stopped mattering. Give `job_slot` its **own
connection, in autocommit**, so the increment is visible the instant it happens.

**Done when** `tests/test_slots.py` and all of `tests/test_migrations.py` are green.

**Then answer in `ANSWERS.md` (3–5 sentences):** your `finally` gives the permit back. Now the machine
running the job loses power, or the process is `SIGKILL`ed. `finally` does not run. `in_use` is stuck at
1 forever, and eventually at 2, and then nothing ever ingests again. Describe one way to make a permit
recover on its own. What would it have to know that the table does not currently record?

---

## 8. Containerise it (~30 min)

Everything so far ran on your laptop against a database in a container. Now the ingest goes in a
container too, and the two have to find each other.

Write a **`Dockerfile`** that builds an image able to run `python -m trip_ingest /data/drops`, and add an
**`ingest`** service to `docker-compose.yml` that:

- builds from that `Dockerfile`;
- waits for `db` to be **healthy** before it starts — not merely for the container to exist. Postgres
  accepts connections several seconds after the container starts, and a bare `depends_on` does not know
  that;
- mounts `./drops` at `/data/drops` and `./rejects` at `/data/rejects`;
- reaches the database.

**That last one is the exercise.** The DSN in `settings.py` — `localhost:55432` — is *your laptop's* view
of Postgres. Inside the `ingest` container, `localhost` is the ingest container itself, where nothing is
listening; and the published port does not exist on that network at all. `settings.database_url()` reads
`DATABASE_URL` from the environment. Work out what it must be, and set it in the compose file.

The e2e test is given, and it is unforgiving:

```bash
uv run pytest -m e2e        # docker compose build --no-cache; up -d db; run --rm ingest
```

It builds your image **from scratch**, brings up the database, writes fresh drops, runs your `ingest`
service, and then connects **from the host** to see whether the rows actually arrived. Then it runs the
ingest a second time and checks that nothing moved — statement 2 again, in a real container this time —
and that the permit was given back.

Note how it is gated: by a **marker**, not an environment variable. Whether an end-to-end test runs is a
question of intent — you ask for it, deliberately, and you wait for it. Where the database lives is a
question of configuration. Those are different questions, and collapsing them into `RUN_E2E=1` gets you a
suite that is green because it ran nothing.

**Done when** `uv run pytest -m e2e` passes from cold. Try `docker compose down -v` first.

**Then answer in `ANSWERS.md` (2–3 sentences):** you now have two DSNs for one database. Name each, say
who uses it, and explain why the container cannot use the host's.

---

## The size gate

`tests/test_size.py` fails if any function in `src/` exceeds **20 code lines** or any file exceeds **250**.
`run_job` is where it bites. It is not a style rule; it is the exercise pointing at the seams.

## Done when

```bash
uv run pytest            # everything except the e2e
uv run pytest -m e2e     # the container, the network, the database
uv run mypy src/
```

`ANSWERS.md` answers Tasks 4, 7 and 8, and everything is pushed.

## Why this matters

Every piece of this exists because a real ingest failed without it. The generator is a machine that ran
out of memory. The primary key is a dashboard that counted every trip twice. The rejects file is a row
that vanished and could not be reconstructed. The permit is a database that fell over at 02:15 because a
cron job overlapped with a retry.

None of them is difficult. What is difficult is holding all of them in one program at once — which is why
this is one program, and not five.
