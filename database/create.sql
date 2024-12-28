PRAGMA foreign_keys = ON;

CREATE TABLE org(
	id       TEXT PRIMARY KEY NOT NULL,
	name     TEXT NOT NULL,
	color_a  TEXT NOT NULL,
	color_b  TEXT NOT NULL,
	icon_url TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE player(
	id     TEXT PRIMARY KEY NOT NULL,
	org    TEXT NOT NULL,
	name   TEXT NOT NULL,
	active BOOLEAN NOT NULL DEFAULT true,

	FOREIGN KEY(org) REFERENCES org(id)
) WITHOUT ROWID;

-- season is not strictly needed since we can derive it from the timestamp
-- but it makes lots of queries simpler
CREATE TABLE game(
	id        TEXT PRIMARY KEY NOT NULL,
	timestamp NUMERIC NOT NULL,
	org       TEXT NOT NULL,
	season    TEXT NOT NULL,

	defense_a TEXT NOT NULL,
	offense_a TEXT NOT NULL,
	defense_b TEXT NOT NULL,
	offense_b TEXT NOT NULL,

	score_a   INT CHECK(score_a >= 0),
	score_b   INT CHECK(score_b >= 0),

	FOREIGN KEY(org) REFERENCES org(id),
	FOREIGN KEY(defense_a) REFERENCES player(id),
	FOREIGN KEY(offense_a) REFERENCES player(id),
	FOREIGN KEY(defense_b) REFERENCES player(id),
	FOREIGN KEY(offense_b) REFERENCES player(id)
);

CREATE INDEX game_season_idx ON game(timestamp, season)
