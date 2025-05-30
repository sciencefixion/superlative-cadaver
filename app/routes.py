from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import Game, Player, Contribution
from app.utils import get_last_fragment
import uuid

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/create', methods=['GET', 'POST'])
def create_game():
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        max_players = int(request.form.get('max_players'))
        rounds = int(request.form.get('rounds'))
        
        # First create and commit the game to get an ID
        new_game = Game(
            name=game_name,
            max_players=max_players,
            rounds=rounds
        )
        db.session.add(new_game)
        db.session.commit()  # This generates the game ID
        
        # Now create players with the game ID
        player_names = request.form.getlist('player_name[]')
        for i, name in enumerate(player_names[:max_players], start=1):
            new_player = Player(
                game_id=new_game.id,  # Now new_game.id exists
                name=name,
                session_id='hotseat',
                position=i
            )
            db.session.add(new_player)
        
        new_game.current_players = len(player_names[:max_players])
        db.session.commit()
        session['game_id'] = new_game.id
        return redirect(url_for('main.switch_player', game_id=new_game.id))
    
    return render_template('create.html')

@bp.route('/join', methods=['GET', 'POST'])
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
        return redirect(url_for('main.play_game', game_id=game.id))
    
    return render_template('join.html')

@bp.route('/switch_player/<game_id>', methods=['GET', 'POST'])
def switch_player(game_id):
    game = Game.query.get_or_404(game_id)

    # Debug output
    print(f"SWITCH - Game Round: {game.current_round}")
    print(f"SWITCH - Players: {game.current_players}")

    if request.method == 'POST':
        player_name = request.form.get('player_name')
        player = Player.query.filter_by(
            game_id=game.id,
            name=player_name
        ).first()
        
        if player:
            session['player_name'] = player.name
            session['player_position'] = player.position
            # Verify the player's position
            print(f"SWITCH - Selected Player: {player.position}")
            
            # Force commit any pending changes
            db.session.commit()
            
            return redirect(url_for('main.play_game', game_id=game.id))
    
    players = Player.query.filter_by(game_id=game.id).order_by(Player.position).all()
    return render_template('switch_player.html', 
                         game=game, 
                         players=players,
                         current_round=game.current_round)

@bp.route('/play/<game_id>', methods=['GET', 'POST'])
def play_game(game_id):
    game = Game.query.get_or_404(game_id)
    player_position = session.get('player_position')
    
      # Debug output - remove after testing
    print(f"Game ID: {game.id}")
    print(f"Current Round: {game.current_round}")
    print(f"Player Position: {player_position}")
    # print(f"Current Turn Position: {current_turn_position}")
    print(f"Total Players: {game.current_players}")

    # Calculate whose turn it is (1, 2, 3... cycling through players)
    print(game.turn_count, game.current_players, player_position)
    mod_turn = (game.turn_count % game.current_players)
    if mod_turn == (player_position - 1):
        is_player_turn = True
    else:
        is_player_turn = False
    print(game.turn_count)

      # More debug output
    # print(f"Updated Current Turn Position: {current_turn_position}")
    print(f"Is Player Turn: {is_player_turn}")

    if request.method == 'POST' and is_player_turn:
        content = request.form.get('content', '').strip()
        if len(content) < 3:
            flash("Contribution must be at least 3 characters")
            return redirect(url_for('main.play_game', game_id=game_id))

        # Save contribution
        Contribution.create(
            game_id=game.id,
            round_number=game.current_round,
            player_position=player_position,
            content=content
        )

        game.turn_count += 1
        print(f"Turn Count: {game.turn_count}")

        # Advance round if last player has gone
        player_id = player_position
        game_players_max = game.current_players
        if player_id == game_players_max:
            game.current_round += 1
            if game.current_round > game.rounds:
                game.is_complete = True
                return redirect(url_for('main.game_over', game_id=game.id))
        print("player_id:", player_id, "game_players_max:", game_players_max, "current_round:", game.current_round)
        game.save()

        return redirect(url_for('main.switch_player', game_id=game.id))

    # Get previous round's contributions
    prev_round = game.current_round - 1
    prev_contributions = Contribution.get_by_round(game.id, prev_round) if prev_round > 0 else []

    return render_template('play.html',
        game=game,
        is_player_turn=is_player_turn,
        current_player_number=player_position,
        previous_contributions=prev_contributions
    )

@bp.route('/view/<game_id>')
def view_game(game_id):
    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('main.index'))
    
    if not game.is_complete:
        return redirect(url_for('main.play_game', game_id=game.id))
    
    contributions = Contribution.query.filter_by(game_id=game.id).order_by(
        Contribution.round_number,
        Contribution.player_position
    ).all()
    
    return render_template('view.html', game=game, contributions=contributions)

@bp.route('/game_over/<game_id>')
def game_over(game_id):
    game = Game.query.get(game_id)
    
    contributions = Contribution.query.filter_by(game_id=game.id).order_by(
        Contribution.round_number,
        Contribution.player_position
    ).all()
    
    return render_template('game_over.html', contributions=contributions, game=game)