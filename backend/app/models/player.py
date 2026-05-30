"""Player model — represents a tournament participant (not a user account)."""
from ..extensions import db


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    in_game_team_name = db.Column(db.String(100), nullable=True)
    favourite_club = db.Column(db.String(100), nullable=True)
    team_image_url = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'name': self.name,
            'in_game_team_name': self.in_game_team_name,
            'favourite_club': self.favourite_club,
            'team_image_url': self.team_image_url,
        }

    def __repr__(self):
        return f'<Player {self.name}>'
