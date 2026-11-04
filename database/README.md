# Database Operations

Helper scripts for the Forsetiemblem Postgres database. All three are run from
the **repository root** and operate on backups stored under `backups/`.

| Script | Purpose | Destructive? | Target |
| ------ | ------- | ------------ | ------ |
| `database/db-dump.sh` | Create a snapshot (backup/export) | No | `local` or `prod` |
| `database/db-restore.sh` | Restore a snapshot | **Yes** (drops + recreates) | `local` only |
| `database/db-reset.sh` | Empty the database | **Yes** (drops + recreates) | `local` only |

## Dump

```bash
bash database/db-dump.sh local   # local Docker Postgres container
bash database/db-dump.sh prod    # production DB via DATABASE_URL
```

Writes a PostgreSQL custom-format archive to `backups/local/` or `backups/prod/`
(named `forsetiemblem-<mode>-YYYYMMDD-HHMMSS.dump`). `backups/` is git-ignored.

- **local** runs `pg_dump` inside the running `forsetiemblem-db` container.
- **prod** runs `pg_dump` from a temporary `postgres:16` client container against
  `DATABASE_URL`, read from `backend/.env.prod` or the environment. The
  `postgresql+psycopg://` prefix is normalized automatically and the password is
  never printed.

## Restore

```bash
bash database/db-restore.sh backups/local/forsetiemblem-local-20261104-171544.dump
bash database/db-restore.sh backups/prod/forsetiemblem-prod-20261104-171544.dump local
```

Restore is **local-only** by design: populating a production database is a
deliberate Supabase operation, not a casual local script. The script terminates
connections, drops and recreates the local database, re-adds the pgvector
extension, then loads the archive with `pg_restore --no-owner`. Pass `-y` to
skip the confirmation prompt.

The restore client is chosen by dump origin:

- **Local dumps** (`backups/local/…`) use the `forsetiemblem-db` container's own
  `pg_restore` — no extra image is pulled.
- **Prod dumps** (`backups/prod/…` or `forsetiemblem-prod-*`) are restored with a
  temporary `postgres:17-alpine` client, because Supabase runs PostgreSQL 17 and
  the local container's PostgreSQL 16 `pg_restore` cannot read a 17-format
  archive. Override the image with `PG_RESTORE_IMAGE` if the server major version
  changes.

## Reset

```bash
bash database/db-reset.sh
```

Drops and recreates the local database and re-adds the pgvector extension,
leaving an empty database. Use this to start clean before a data-related test,
then restart the backend so migrations recreate the tables.

## Typical workflow

```bash
bash database/db-dump.sh local                       # save current state first
bash database/db-reset.sh                            # start clean
bash database/db-restore.sh backups/local/<file>.dump  # load a snapshot back
```

Inspect any archive without restoring:

```bash
pg_restore --list <file>.dump
```
