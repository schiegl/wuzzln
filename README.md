# wuzzln

Table football (or _wuzzln_ in Austria) leaderboard for your organization or group.

## Features
- Player leaderboard with ranks
- ELO-like rating for each player (defense and offense) using Trueskill
- Tracking of game results & player statistics
- Fair team assignments based on rating
- Quarterly seasons with visual recap


## Maintenance

The schema of the database can be found at: `database/create.sql`. When using `run.sh` to run the service, the database will be mounted at `~/database/db.sqlite`, where `~/database/` must be writable by the container. There is no user management in the web UI, therefore it has to be done manually with the sqlite database.


### Open database

The simplest way to update the database is to open it in an interactive session with `sqlite3`.

```sh
cp ~/database/db.sqlite ~/db.sqlite.bak  # optional backup
sqlite3 ~/database/db.sqlite
```

### Add player

Adding a player is simply adding a new row to the `player` table.

```sql
INSERT INTO player VALUES ('bob_id', 'bobs_org_id', 'Bob', 1);
```

### Remove player

To keep history and ratings, players are not removed but set inactive. This will remove them from all player select mechanisms (e.g. dropdown for matchmaking).

```sql
UPDATE player SET active=0 WHERE id IN ('bob_id', 'alice_id');
```
