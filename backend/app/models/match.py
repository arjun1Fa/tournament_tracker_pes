"""Match model."""
from datetime import datetime, timezone

from ..extensions import db


class Match(db.Model):
    """Represents a single fixture between two players in a tournament."""
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False
    )
    round = db.Column(db.String(50), nullable=False)  # "Round 1", "Group A", "QF", etc.
    match_order = db.Column(db.Integer, nullable=False, default=0)  # For bracket ordering

    # Players
    player1_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    player2_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True  # Nullable for BYE
    )

    # OCR-extracted team names
    team1_name = db.Column(db.String(100), nullable=True)
    team2_name = db.Column(db.String(100), nullable=True)

    # Score
    score1 = db.Column(db.Integer, nullable=True)
    score2 = db.Column(db.Integer, nullable=True)

    # Status & verification
    status = db.Column(
        db.String(30), nullable=False, default='scheduled'
    )  # scheduled, pending_verification, verified, disputed
    reported_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True
    )
    verified_by_player1 = db.Column(db.Boolean, default=False, nullable=False)
    verified_by_player2 = db.Column(db.Boolean, default=False, nullable=False)
    admin_resolved = db.Column(db.Boolean, default=False, nullable=False)

    # Optional screenshot URL (for dispute evidence)
    screenshot_url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    player1 = db.relationship('User', foreign_keys=[player1_id], backref='home_matches')
    player2 = db.relationship('User', foreign_keys=[player2_id], backref='away_matches')
    reporter = db.relationship('User', foreign_keys=[reported_by])
    stats = db.relationship(
        'MatchStats', backref='match', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def is_bye(self):
        """Check if this match is a BYE (no opponent)."""
        return self.player2_id is None

    def to_dict(self, include_stats=False):
        """Serialize match to dictionary."""
        data = {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'round': self.round,
            'match_order': self.match_order,
            'player1_id': self.player1_id,
            'player1_username': self.player1.username if self.player1 else None,
            'player2_id': self.player2_id,
            'player2_username': self.player2.username if self.player2 else None,
            'team1_name': self.team1_name,
            'team2_name': self.team2_name,
            'score1': self.score1,
            'score2': self.score2,
            'status': self.status,
            'reported_by': self.reported_by,
            'verified_by_player1': self.verified_by_player1,
            'verified_by_player2': self.verified_by_player2,
            'admin_resolved': self.admin_resolved,
            'screenshot_url': self.screenshot_url,
            'is_bye': self.is_bye,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_stats:
            data['stats'] = [s.to_dict() for s in self.stats]
        return data

    def __repr__(self):
        return f'<Match {self.id}: {self.player1_id} vs {self.player2_id}>'
