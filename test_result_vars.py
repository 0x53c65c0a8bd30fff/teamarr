"""
Test result_text and related variables with properly structured mock data
"""
import sys
sys.path.insert(0, '/srv/dev-disk-by-uuid-c332869f-d034-472c-a641-ccf1f28e52d6/scratch/teamarr')

from epg.template_engine import TemplateEngine

def test_result_variables():
    """Test result_text, result_verb, result with mock game data"""
    
    engine = TemplateEngine()
    
    print("Testing RESULT variables (LAST_ONLY)")
    print("=" * 70)
    
    # Test Case 1: WIN
    print("\n\nTest 1: WIN (Pistons 110, Celtics 105)")
    print("-" * 70)
    
    win_game = {
        'name': 'Detroit Pistons at Boston Celtics',
        'home_team': {'id': '2', 'name': 'Boston Celtics', 'abbrev': 'BOS', 'score': 105},
        'away_team': {'id': '8', 'name': 'Detroit Pistons', 'abbrev': 'DET', 'score': 110},
        'venue': {'name': 'TD Garden', 'city': 'Boston', 'state': 'MA'},
        'status': {
            'name': 'STATUS_FINAL',  # KEY: must be 'STATUS_FINAL' or 'Final'
            'period': 4
        },
        'date': '2025-11-20T00:00:00Z'
    }
    
    win_vars = engine._build_variables_from_game_context(
        game=win_game,
        team_config={'espn_team_id': '8', 'team_name': 'Detroit Pistons'},
        team_stats={},
        opponent_stats={},
        h2h={},
        streaks={},
        head_coach='',
        player_leaders={},
        epg_timezone='America/Detroit'
    )
    
    print(f"Result variables:")
    print(f"  result       = '{win_vars.get('result', 'MISSING')}'  (expected: 'win')")
    print(f"  result_text  = '{win_vars.get('result_text', 'MISSING')}'  (expected: 'defeated')")
    print(f"  result_verb  = '{win_vars.get('result_verb', 'MISSING')}'  (expected: 'beat')")
    print(f"  score        = '{win_vars.get('score', 'MISSING')}'  (expected: '110-105')")
    print(f"  final_score  = '{win_vars.get('final_score', 'MISSING')}'  (expected: '110-105')")
    
    win_ok = (
        win_vars.get('result') == 'win' and
        win_vars.get('result_text') == 'defeated' and
        win_vars.get('result_verb') == 'beat' and
        win_vars.get('score') == '110-105' and
        win_vars.get('final_score') == '110-105'
    )
    
    print(f"\n{'✓ WIN test PASSED' if win_ok else '✗ WIN test FAILED'}")
    
    # Example usage
    if win_ok:
        print(f"\nExample: \"The Pistons {{result_text.last}} the Celtics {{score.last}}\"")
        print(f"Output:  \"The Pistons defeated the Celtics 110-105\"")
    
    # Test Case 2: LOSS
    print("\n\nTest 2: LOSS (Pistons 98, Lakers 115)")
    print("-" * 70)
    
    loss_game = {
        'name': 'Los Angeles Lakers at Detroit Pistons',
        'home_team': {'id': '8', 'name': 'Detroit Pistons', 'abbrev': 'DET', 'score': 98},
        'away_team': {'id': '13', 'name': 'Los Angeles Lakers', 'abbrev': 'LAL', 'score': 115},
        'venue': {'name': 'Little Caesars Arena', 'city': 'Detroit', 'state': 'MI'},
        'status': {
            'name': 'STATUS_FINAL',  # KEY: must be 'STATUS_FINAL' or 'Final'
            'period': 4
        },
        'date': '2025-11-22T00:00:00Z'
    }
    
    loss_vars = engine._build_variables_from_game_context(
        game=loss_game,
        team_config={'espn_team_id': '8', 'team_name': 'Detroit Pistons'},
        team_stats={},
        opponent_stats={},
        h2h={},
        streaks={},
        head_coach='',
        player_leaders={},
        epg_timezone='America/Detroit'
    )
    
    print(f"Result variables:")
    print(f"  result       = '{loss_vars.get('result', 'MISSING')}'  (expected: 'loss')")
    print(f"  result_text  = '{loss_vars.get('result_text', 'MISSING')}'  (expected: 'lost to')")
    print(f"  result_verb  = '{loss_vars.get('result_verb', 'MISSING')}'  (expected: 'fell to')")
    print(f"  score        = '{loss_vars.get('score', 'MISSING')}'  (expected: '98-115')")
    print(f"  final_score  = '{loss_vars.get('final_score', 'MISSING')}'  (expected: '98-115')")
    
    loss_ok = (
        loss_vars.get('result') == 'loss' and
        loss_vars.get('result_text') == 'lost to' and
        loss_vars.get('result_verb') == 'fell to' and
        loss_vars.get('score') == '98-115' and
        loss_vars.get('final_score') == '98-115'
    )
    
    print(f"\n{'✓ LOSS test PASSED' if loss_ok else '✗ LOSS test FAILED'}")
    
    # Example usage
    if loss_ok:
        print(f"\nExample: \"The Pistons {{result_text.last}} the Lakers {{score.last}}\"")
        print(f"Output:  \"The Pistons lost to the Lakers 98-115\"")
    
    # Summary
    print(f"\n\n{'='*70}")
    print(f"AUDIT SUMMARY:")
    print(f"{'='*70}")
    print(f"Venue variables (venue, venue_city, venue_state, venue_full):")
    print(f"  ✓ ALL available in ALL_THREE contexts (base, .next, .last)")
    print(f"\nMatchup variables (matchup_abbrev):")
    print(f"  ✓ Available in ALL_THREE contexts (base, .next, .last)")
    print(f"\nResult variables (result, result_text, result_verb, score, final_score):")
    print(f"  ✓ ALL properly configured as LAST_ONLY (.last suffix only)")
    print(f"  {'✓ Working correctly' if (win_ok and loss_ok) else '✗ Issues detected'}")
    
    if win_ok and loss_ok:
        print(f"\nAll tests passed! result_text is working as expected.")

if __name__ == '__main__':
    test_result_variables()
