"""Match model — a single fixture with full stats."""
from datetime import datetime, timezone
from ..extensions import db


class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    round_name = db.Column(db.String(100), nullable=False)   # "Matchday 1", "Semi-Final", "Final"
    stage = db.Column(db.String(20), nullable=False, default='league')  # 'league' or 'playoff'
    match_order = db.Column(db.Integer, nullable=False, default=0)

    player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)

    # Result & Stats
    score1 = db.Column(db.Integer, nullable=True)
    score2 = db.Column(db.Integer, nullable=True)
    possession1 = db.Column(db.Integer, nullable=True)   # % for player1
    possession2 = db.Column(db.Integer, nullable=True)
    shots1 = db.Column(db.Integer, nullable=True)
    shots2 = db.Column(db.Integer, nullable=True)
    shots_on_target1 = db.Column(db.Integer, nullable=True)
    shots_on_target2 = db.Column(db.Integer, nullable=True)

    status = db.Column(db.String(20), nullable=False, default='scheduled')  # scheduled / completed
    completed_at = db.Column(db.DateTime, nullable=True)

    # Playoff bracket advancement
    next_match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=True)
    next_match_slot = db.Column(db.Integer, nullable=True)  # 1 or 2

    # Relationships
    player1 = db.relationship('Player', foreign_keys=[player1_id])
    player2 = db.relationship('Player', foreign_keys=[player2_id])

    def performance_score(self, slot: int) -> float:
        """Compute a composite performance score for player in slot 1 or 2."""
        if slot == 1:
            goals = self.score1 or 0
            poss = self.possession1 or 0
            sot = self.shots_on_target1 or 0
            shots = self.shots1 or 0
        else:
            goals = self.score2 or 0
            poss = self.possession2 or 0
            sot = self.shots_on_target2 or 0
            shots = self.shots2 or 0
        return goals * 5.0 + poss * 0.3 + sot * 1.5 + shots * 0.5

    def better_performer(self):
        """Return 1 or 2 (slot) of the player who performed better, or 0 if draw."""
        if self.status != 'completed':
            return None
        s1 = self.performance_score(1)
        s2 = self.performance_score(2)
        if s1 > s2:
            return 1
        elif s2 > s1:
            return 2
        return 0

    def winner_player_id(self):
        """Return the player_id of the match winner for playoff advancement."""
        if self.status != 'completed':
            return None
        if self.score1 > self.score2:
            return self.player1_id
        elif self.score2 > self.score1:
            return self.player2_id
        # On draw, higher performance score wins (shouldn't happen in playoff, but fallback)
        bp = self.better_performer()
        if bp == 1:
            return self.player1_id
        elif bp == 2:
            return self.player2_id
        return self.player1_id  # absolute fallback

    def to_dict(self):
        performer = self.better_performer()
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'round_name': self.round_name,
            'stage': self.stage,
            'match_order': self.match_order,
            'player1_id': self.player1_id,
            'player1_name': self.player1.name if self.player1 else 'TBD',
            'player1_team': self.player1.in_game_team_name if self.player1 else None,
            'player1_image': self.player1.team_image_url if self.player1 else None,
            'player2_id': self.player2_id,
            'player2_name': self.player2.name if self.player2 else 'TBD',
            'player2_team': self.player2.in_game_team_name if self.player2 else None,
            'player2_image': self.player2.team_image_url if self.player2 else None,
            'score1': self.score1,
            'score2': self.score2,
            'possession1': self.possession1,
            'possession2': self.possession2,
            'shots1': self.shots1,
            'shots2': self.shots2,
            'shots_on_target1': self.shots_on_target1,
            'shots_on_target2': self.shots_on_target2,
            'status': self.status,
            'better_performer_slot': performer,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<Match {self.id}: {self.player1_id} vs {self.player2_id}>'
