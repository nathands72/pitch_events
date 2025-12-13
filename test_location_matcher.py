"""
Test semantic location matching functionality.
"""
from utils.location_matcher import matches_location


def test_exact_matches():
    """Test exact location matches."""
    print("Testing exact matches...")
    
    # Exact city match
    assert matches_location("Bangalore", "Bangalore", "India") == True
    print("[PASS] Bangalore matches Bangalore, India")
    
    # Alternative name
    assert matches_location("Bengaluru", "Bangalore", "India") == True
    print("[PASS] Bengaluru matches Bangalore, India")
    
    # Case insensitive
    assert matches_location("bangalore", "Bangalore", "India") == True
    print("[PASS] bangalore matches Bangalore, India (case insensitive)")


def test_regional_matches():
    """Test regional location matches."""
    print("\nTesting regional matches...")
    
    # Bay Area should match San Francisco
    assert matches_location("Bay Area", "San Francisco", "USA") == True
    print("[PASS] Bay Area matches San Francisco, USA")
    
    # Silicon Valley should match San Jose
    assert matches_location("Silicon Valley", "San Jose", "USA") == True
    print("[PASS] Silicon Valley matches San Jose, USA")


def test_country_matches():
    """Test country-level matches."""
    print("\nTesting country matches...")
    
    # India should match Bangalore
    assert matches_location("India", "Bangalore", "India") == True
    print("[PASS] India matches Bangalore, India")
    
    # USA should match New York
    assert matches_location("USA", "New York", "USA") == True
    print("[PASS] USA matches New York, USA")


def test_non_matches():
    """Test locations that should NOT match."""
    print("\nTesting non-matches...")
    
    # Different cities
    assert matches_location("London", "Paris", "France") == False
    print("[PASS] London does NOT match Paris, France")
    
    # Different countries
    assert matches_location("Tokyo", "New York", "USA") == False
    print("[PASS] Tokyo does NOT match New York, USA")


def test_nearby_cities():
    """Test nearby cities in same metro area."""
    print("\nTesting nearby cities...")
    
    # San Jose is close to San Francisco
    result = matches_location("San Francisco", "San Jose", "USA")
    print(f"  San Francisco vs San Jose, USA = {result}")
    
    # Gurgaon is close to Delhi
    result = matches_location("Delhi", "Gurgaon", "India")
    print(f"  Delhi vs Gurgaon, India = {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("SEMANTIC LOCATION MATCHING TESTS")
    print("=" * 60)
    
    try:
        test_exact_matches()
        test_regional_matches()
        test_country_matches()
        test_non_matches()
        test_nearby_cities()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
