from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import uuid
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Game(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    current_players = db.Column(db.Integer, default=1)
    rounds = db.Column(db.Integer, nullable=False)
    current_round = db.Column(db.Integer, default=1)
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

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

def get_last_fragment(text, fragment_size=1):
    """Return the last fragment of text (sentence or line)"""
    sentences = text.split('.')
    if len(sentences) > fragment_size:
        return '.'.join(sentences[-fragment_size-1:-1]) + '.' if fragment_size > 1 else sentences[-2] + '.'
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create_game():
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        max_players = int(request.form.get('max_players'))
        rounds = int(request.form.get('rounds'))
        
        new_game = Game(
            name=game_name,
            max_players=max_players,
            rounds=rounds
        )
        db.session.add(new_game)
        
        player_names = request.form.getlist('player_name[]')
        for i, name in enumerate(player_names[:max_players], start=1):
            new_player = Player(
                game_id=new_game.id,
                name=name,
                session_id='hotseat',
                position=i
            )
            db.session.add(new_player)
        
        new_game.current_players = len(player_names[:max_players])
        db.session.commit()
        session['game_id'] = new_game.id
        return redirect(url_for('switch_player', game_id=new_game.id))
    
    return render_template('create.html')

@app.route('/join', methods=['GET', 'POST'])
def join_game():
    if request.method == 'POST':
        game_id = request.form.get('game_id')
        player_name = request.form.get('player_name')
        
        game = Game.query.get(game_id)
        if not game:
            flash("Game not found")
            return render_template('join.html')
        
        if game.current_players >= game.max_players:
            flash("Game is full")
            return render_template('join.html')
        
        if game.is_complete:
            flash("Game is already complete")
            return render_template('join.html')
        
        new_player = Player(
            game_id=game.id,
            name=player_name,
            session_id=session.sid,
            position=game.current_players + 1
        )
        db.session.add(new_player)
        game.current_players += 1
        db.session.commit()
        
        session['game_id'] = game.id
        session['player_name'] = player_name
        session['player_position'] = new_player.position
        return redirect(url_for('play_game', game_id=game.id))
    
    return render_template('join.html')

@app.route('/switch_player/<game_id>', methods=['GET', 'POST'])
def switch_player(game_id):
    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        player_name = request.form.get('player_name')
        player = Player.query.filter_by(
            game_id=game.id,
            name=player_name
        ).first()
        
        if player:
            session['player_name'] = player.name
            session['player_position'] = player.position
            return redirect(url_for('play_game', game_id=game.id))
    
    players = Player.query.filter_by(game_id=game.id).order_by(Player.position).all()
    return render_template('switch_player.html', 
                         game=game, 
                         players=players)

@app.route('/play/<game_id>', methods=['GET', 'POST'])
def play_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('index'))
    
    current_player_position = (game.current_round - 1) % game.current_players + 1
    
    if request.method == 'POST':
        content = request.form.get('content')
        if not content or len(content.strip()) < 3:
            flash("Please enter at least 3 characters")
            return redirect(url_for('play_game', game_id=game.id))
        
        player_position = int(request.form.get('player_position'))
        new_contribution = Contribution(
            game_id=game.id,
            round_number=game.current_round,
            player_position=player_position,
            content=content.strip()
        )
        db.session.add(new_contribution)
        
        if player_position == game.current_players:
            game.current_round += 1
        
        db.session.commit()
        return redirect(url_for('switch_player', game_id=game.id))
    
    prev_player = current_player_position - 1 if current_player_position > 1 else None
    previous_contribution = None
    if prev_player:
        contribution = Contribution.query.filter_by(
            game_id=game.id,
            player_position=prev_player,
            round_number=game.current_round
        ).first()
        
        if contribution:
            previous_contribution = get_last_fragment(contribution.content)
    
    return render_template('play.html', 
                         game=game, 
                         current_player_position=current_player_position,
                         previous_contribution=previous_contribution)

@app.route('/view/<game_id>')
def view_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('index'))
    
    if not game.is_complete:
        return redirect(url_for('play_game', game_id=game.id))
    
    contributions = Contribution.query.filter_by(game_id=game.id).order_by(
        Contribution.round_number,
        Contribution.player_position
    ).all()
    
    return render_template('view.html', game=game, contributions=contributions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)