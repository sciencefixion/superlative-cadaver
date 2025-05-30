from .extensions import db
import uuid

class Game(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    current_players = db.Column(db.Integer, default=1)
    rounds = db.Column(db.Integer, nullable=False)
    current_round = db.Column(db.Integer, default=0)
    turn_count = db.Column(db.Integer, default=0)
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def verify_turn(self, player_position):
        expected_position = ((self.current_round - 1) % self.current_players) + 1
        return player_position == expected_position

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(36), db.ForeignKey('game.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    position = db.Column(db.Integer, nullable=False)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(36), db.ForeignKey('game.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    player_position = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    __table_args__ = (
        db.Index('ix_game_round', 'game_id', 'round_number'),
    )

    @classmethod
    def create(cls, **kwargs):
        contribution = cls(**kwargs)
        db.session.add(contribution)
        db.session.commit()
        return contribution
    
    @classmethod
    def get_by_round(cls, game_id, round_number):
        return cls.query.filter_by(
            game_id=game_id,
            round_number=round_number
        ).order_by(cls.player_position).all()


