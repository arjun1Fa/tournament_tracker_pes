-- =============================================
-- eFootball Tournament Tracker - Database Schema
-- Run this in Supabase SQL Editor
-- =============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    profile_picture VARCHAR(256),
    platform VARCHAR(50),
    favourite_club VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    is_suspended BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Device tokens (for push notifications)
CREATE TABLE IF NOT EXISTS device_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    format VARCHAR(50) NOT NULL DEFAULT 'league',
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    is_public BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(256),
    max_participants INTEGER DEFAULT 8,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tournament participants (join table)
CREATE TABLE IF NOT EXISTS tournament_participants (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seed INTEGER,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tournament_id, user_id)
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    round VARCHAR(100) NOT NULL,
    match_order INTEGER NOT NULL DEFAULT 0,
    player1_id INTEGER REFERENCES users(id),
    player2_id INTEGER REFERENCES users(id),
    team1_name VARCHAR(100),
    team2_name VARCHAR(100),
    score1 INTEGER,
    score2 INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    verified_by_player1 BOOLEAN DEFAULT FALSE,
    verified_by_player2 BOOLEAN DEFAULT FALSE,
    reported_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Match stats (detailed per-player stats)
CREATE TABLE IF NOT EXISTS match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    team_name VARCHAR(100) NOT NULL,
    possession FLOAT,
    shots INTEGER,
    shots_on_target INTEGER,
    fouls INTEGER,
    offsides INTEGER,
    corner_kicks INTEGER,
    free_kicks INTEGER,
    passes INTEGER,
    successful_passes INTEGER,
    crosses INTEGER,
    interceptions INTEGER,
    tackles INTEGER,
    saves INTEGER
);

-- Indexes for performance
CREATE INDEX idx_matches_tournament ON matches(tournament_id);
CREATE INDEX idx_matches_player1 ON matches(player1_id);
CREATE INDEX idx_matches_player2 ON matches(player2_id);
CREATE INDEX idx_match_stats_match ON match_stats(match_id);
CREATE INDEX idx_participants_tournament ON tournament_participants(tournament_id);
CREATE INDEX idx_device_tokens_user ON device_tokens(user_id);

-- Seed the admin user (WinterFA)
-- Password will be set via the ADMIN_PASSWORD env var when the app first starts.
-- The app's seed_admin() function handles this automatically.
