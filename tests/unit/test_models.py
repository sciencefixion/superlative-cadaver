from app import db
from models import Game, Player, Contribution
from datetime import datetime

def test_game_creation(sample_game):
    assert sample_game.name == "Test Game"
    assert sample_game.max_players == 3
    assert sample_game.rounds == 2
    assert isinstance(sample_game.created_at, datetime)

def test_player_relationships(sample_game, sample_players):
    assert sample_game.players.count() == 3
    assert sample_players[0].game == sample_game