import pytest
from app import app, db
from models import Game, Player, Contribution
import os

@pytest.fixture
def client():
  app.config['TESTING'] = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
  app.config['WTF_CSRF_ENABLED'] = False

  with app.test_client() as client:
    with app.app_context():
      db.create_all()
      yield client
      with app.app_context():
        db.drop_all()

@pytest.fixture
def sample_game(client):
    game = Game(name="Test Game", max_players=3, rounds=2)
    db.session.add(game)
    db.session.commit()
    return game

@pytest.fixture
def sample_players(sample_game):
    players = [
        Player(name="Laura", session_id="123", position=1),
        Player(name="Bob", session_id="456", position=2),
        Player(name="Cooper", session_id="789", position=3)
    ]
    db.session.add_all(players)
    db.session.commit()
    return players

@pytest.fixture
def sample_contributions(sample_game, sample_players):
    contributions = [
        Contribution(game_id=sample_game.id, round_number=1, player_position=1, content="Once upon a time"),
        Contribution(game_id=sample_game.id, round_number=1, player_position=2, content="there was a fish in the percolator")
    ]
    db.session.add_all(contributions)
    db.session.commit()
    return contributions