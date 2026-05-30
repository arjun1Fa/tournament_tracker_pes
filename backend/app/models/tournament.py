"""Tournament model."""
from datetime import datetime, timezone
from ..extensions import db


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    # registration -> league_ongoing -> playoffs_ongoing -> completed
    status = db.Column(db.String(30), nullable=False, default='registration')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    players = db.relationship('Player', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_players=False):
        data = {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'player_count': self.players.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_players:
            data['players'] = [p.to_dict() for p in self.players.order_by('id')]
        return data

    def __repr__(self):
        return f'<Tournament {self.name}>'
