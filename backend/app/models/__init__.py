"""Database models package.

Import all models here so Flask-Migrate can discover them.
"""
from .user import User, DeviceToken
from .tournament import Tournament, TournamentParticipant
from .match import Match
from .match_stats import MatchStats

__all__ = [
    'User',
    'DeviceToken',
    'Tournament',
    'TournamentParticipant',
    'Match',
    'MatchStats',
]
