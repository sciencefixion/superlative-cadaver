def test_full_hotseat_game_flow(client):
    """Test complete hotseat game flow from creation to completion"""
    # Step 1: Create game
    data = {
        'game_name': 'Full Flow Test',
        'max_players': '2',
        'rounds': '1',
        'player_name[]': ['Player1', 'Player2']
    }
    response = client.post('/create', data=data, follow_redirects=True)
    assert b"Switch Player" in response.data
    
    # Get game ID from redirect URL
    game_id = response.request.path.split('/')[-1]
    
    # Step 2: Player 1's turn
    response = client.post(f'/switch_player/{game_id}', data={
        'player_name': 'Player1',
        'player_position': 1
    }, follow_redirects=True)
    assert b"Your Turn" in response.data
    
    # Submit Player 1's contribution
    response = client.post(f'/play/{game_id}', data={
        'content': 'Player 1 contribution',
        'player_position': 1
    }, follow_redirects=True)
    assert b"Switch Player" in response.data
    
    # Step 3: Player 2's turn
    response = client.post(f'/switch_player/{game_id}', data={
        'player_name': 'Player2',
        'player_position': 2
    }, follow_redirects=True)
    assert b"Your Turn" in response.data
    
    # Submit Player 2's contribution (completes game)
    response = client.post(f'/play/{game_id}', data={
        'content': 'Player 2 contribution',
        'player_position': 2
    }, follow_redirects=True)
    assert b"Final Result" in response.data
    assert b"Player 1 contribution" in response.data
    assert b"Player 2 contribution" in response.data