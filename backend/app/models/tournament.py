"""Tournament and TournamentParticipant models."""
from datetime import datetime, timezone

import bcrypt

from ..extensions import db


class Tournament(db.Model):
    """Represents a tournament (e.g., EFL Season I)."""
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # For private tournaments
    max_participants = db.Column(db.Integer, nullable=False, default=10)
    format = db.Column(
        db.String(50), nullable=False, default='round_robin'
    )  # round_robin, swiss, single_elim, double_elim, group_knockout, efl
    status = db.Column(
        db.String(20), nullable=False, default='open'
    )  # open, ongoing, completed
    created_by = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False
    )
    rules = db.Column(db.JSON, nullable=True, default=dict)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator = db.relationship('User', backref='created_tournaments', foreign_keys=[created_by])
    participants = db.relationship(
        'TournamentParticipant', backref='tournament', lazy='dynamic',
        cascade='all, delete-orphan',
    )
    matches = db.relationship(
        'Match', backref='tournament', lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def set_password(self, password):
        """Hash the tournament join password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), salt
        ).decode('utf-8')

    def check_password(self, password):
        """Verify the tournament join password."""
        if not self.password_hash:
            return True
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'),
        )

    @property
    def participant_count(self):
        """Current number of participants."""
        return self.participants.count()

    def to_dict(self, include_participants=False):
        """Serialize tournament to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'is_public': self.is_public,
            'has_password': self.password_hash is not None,
            'max_participants': self.max_participants,
            'participant_count': self.participant_count,
            'format': self.format,
            'status': self.status,
            'created_by': self.created_by,
            'creator_username': self.creator.username if self.creator else None,
            'rules': self.rules,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_participants:
            data['participants'] = [p.to_dict() for p in self.participants]
        return data

    def __repr__(self):
        return f'<Tournament {self.name}>'


class TournamentParticipant(db.Model):
    """Links a user to a tournament with seeding and final rank."""
    __tablename__ = 'tournament_participants'
    __table_args__ = (
        db.UniqueConstraint('tournament_id', 'user_id', name='uq_tournament_user'),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    seed = db.Column(db.Integer, nullable=True)
    final_rank = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        """Serialize participant to dictionary."""
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'seed': self.seed,
            'final_rank': self.final_rank,
        }

    def __repr__(self):
        return f'<TournamentParticipant t={self.tournament_id} u={self.user_id}>'
