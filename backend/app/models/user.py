"""User and DeviceToken models."""
from datetime import datetime, timezone

import bcrypt

from ..extensions import db


class User(db.Model):
    """Represents a player or admin in the system."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    profile_picture = db.Column(db.String(500), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # e.g., "PS5", "Mobile"
    favourite_club = db.Column(db.String(100), nullable=True)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    device_tokens = db.relationship(
        'DeviceToken', backref='user', lazy='dynamic', cascade='all, delete-orphan'
    )
    tournament_participations = db.relationship(
        'TournamentParticipant', backref='user', lazy='dynamic', cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and store the password using bcrypt."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), salt
        ).decode('utf-8')

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'),
        )

    def to_dict(self, include_email=False):
        """Serialize user to dictionary. Never includes password_hash."""
        data = {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'profile_picture': self.profile_picture,
            'platform': self.platform,
            'favourite_club': self.favourite_club,
            'is_suspended': self.is_suspended,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
        return data

    def __repr__(self):
        return f'<User {self.username}>'


class DeviceToken(db.Model):
    """Stores FCM device tokens for push notifications."""
    __tablename__ = 'device_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    fcm_token = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # "ios" or "android"
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f'<DeviceToken user={self.user_id} platform={self.platform}>'
