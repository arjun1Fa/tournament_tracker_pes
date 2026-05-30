"""MatchStats model — per-player stats extracted from OCR."""
from ..extensions import db


class MatchStats(db.Model):
    """Stores detailed stats for one player's side of a match.

    Each verified match has exactly two MatchStats rows (one per player).
    Stats are extracted via OCR from the eFootball post-match screen.
    """
    __tablename__ = 'match_stats'
    __table_args__ = (
        db.UniqueConstraint('match_id', 'user_id', name='uq_match_user_stats'),
    )

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer, db.ForeignKey('matches.id', ondelete='CASCADE'), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    team_name = db.Column(db.String(100), nullable=True)  # e.g., "joshua", "La Remontada"

    # All 13 stats from the eFootball post-match screen
    possession = db.Column(db.Float, nullable=True)         # Percentage (e.g., 51.0)
    shots = db.Column(db.Integer, nullable=True)
    shots_on_target = db.Column(db.Integer, nullable=True)
    fouls = db.Column(db.Integer, nullable=True)
    offsides = db.Column(db.Integer, nullable=True)
    corner_kicks = db.Column(db.Integer, nullable=True)
    free_kicks = db.Column(db.Integer, nullable=True)
    passes = db.Column(db.Integer, nullable=True)
    successful_passes = db.Column(db.Integer, nullable=True)
    crosses = db.Column(db.Integer, nullable=True)
    interceptions = db.Column(db.Integer, nullable=True)
    tackles = db.Column(db.Integer, nullable=True)
    saves = db.Column(db.Integer, nullable=True)

    # Relationship
    user = db.relationship('User', backref='match_stats')

    def to_dict(self):
        """Serialize stats to dictionary."""
        return {
            'id': self.id,
            'match_id': self.match_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'team_name': self.team_name,
            'possession': self.possession,
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,
            'fouls': self.fouls,
            'offsides': self.offsides,
            'corner_kicks': self.corner_kicks,
            'free_kicks': self.free_kicks,
            'passes': self.passes,
            'successful_passes': self.successful_passes,
            'crosses': self.crosses,
            'interceptions': self.interceptions,
            'tackles': self.tackles,
            'saves': self.saves,
        }

    def __repr__(self):
        return f'<MatchStats match={self.match_id} user={self.user_id}>'
