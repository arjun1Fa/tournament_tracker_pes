-- Drop existing tables
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS tournaments CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Create admins table
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL
);

-- Create tournaments table
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'registration',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    in_game_team_name VARCHAR(100),
    favourite_club VARCHAR(100),
    team_image_url VARCHAR(500)
);

-- Create matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    round_name VARCHAR(100) NOT NULL,
    stage VARCHAR(20) NOT NULL DEFAULT 'league',
    match_order INTEGER NOT NULL DEFAULT 0,
    player1_id INTEGER REFERENCES players(id),
    player2_id INTEGER REFERENCES players(id),
    score1 INTEGER,
    score2 INTEGER,
    possession1 INTEGER,
    possession2 INTEGER,
    shots1 INTEGER,
    shots2 INTEGER,
    shots_on_target1 INTEGER,
    shots_on_target2 INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    completed_at TIMESTAMP WITH TIME ZONE,
    next_match_id INTEGER REFERENCES matches(id),
    next_match_slot INTEGER
);
