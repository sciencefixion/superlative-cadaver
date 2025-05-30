from app import get_last_fragment

def test_get_last_fragment():
    """Test the get_last_fragment utility function"""
    # Test with multiple sentences
    text = "First sentence. Second sentence. Third sentence."
    assert get_last_fragment(text) == "Third sentence."
    
    # Test with one sentence
    assert get_last_fragment("Only one sentence") == "Only one sentence"
    
    # Test with empty string
    assert get_last_fragment("") == ""
    
    # Test with custom fragment size
    assert get_last_fragment("One. Two. Three.", 2) == "Two. Three."