def test_index_route(client):
    """Test the index route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Exquisite Corpse" in response.data

def test_create_game_route(client):
    """Test game creation flow"""
    # Test GET request
    response = client.get('/create')
    assert response.status_code == 200
    
    # Test POST request
    data = {
        'game_name': 'Integration Test Game',
        'max_players': '3',
        'rounds': '2',
        'player_name[]': ['Laura', 'Bob', 'Cooper']
    }
    response = client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Switch Player" in response.data  # Should redirect to player switch

def test_play_route(client, sample_game, sample_players):
    """Test the play route"""
    # Set up session
    with client.session_transaction() as session:
        session['game_id'] = sample_game.id
        session['player_name'] = "Laura"
        session['player_position'] = 1
    
    # Test GET request
    response = client.get(f'/play/{sample_game.id}')
    assert response.status_code == 200
    assert b"Your Turn" in response.data
    
    # Test POST request
    response = client.post(f'/play/{sample_game.id}', data={
        'content': 'Test contribution',
        'player_position': 1
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Switch Player" in response.data  # Should redirect to player switch

def test_game_completion(client, sample_game, sample_players, sample_contributions):
    """Test full game completion flow"""
    # Simulate all rounds
    sample_game.current_round = 2
    db.session.commit()
    
    # Last player's turn
    with client.session_transaction() as session:
        session['game_id'] = sample_game.id
        session['player_name'] = "Cooper"
        session['player_position'] = 3
    
    # Submit final contribution
    response = client.post(f'/play/{sample_game.id}', data={
        'content': 'The end',
        'player_position': 3
    }, follow_redirects=True)
    
    # Should redirect to view game
    assert response.status_code == 200
    assert b"Final Result" in response.data