"""
Test the parser fix with various scenarios including the original error case.
"""
from agents.parser_agent import ParserAgent

def test_case(name, data):
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    
    parser = ParserAgent()
    result = parser.parse(data, source="tavily")
    
    if result:
        print("[SUCCESS] Parsed event!")
        print(f"  Title: {result.title}")
        print(f"  Start Date: {result.start_utc}")
        print(f"  Tags: {result.tags}")
        print(f"  Pitch Slots: {result.pitch_slots.available if result.pitch_slots else 'None'}")
    else:
        print("[FAILED] Could not parse event")
    
    return result

# Test 1: Original error case - "Startup Fundraising Summit"
test1_data = {
    'url': 'https://example.com/startup-fundraising-summit',
    'snippet': 'Join us for the Startup Fundraising Summit - By Investors, For Founders. Network with top VCs and angel investors. Apply to pitch your startup.',
    'title': 'Startup Fundraising Summit - By Investors, For Founders'
}

# Test 2: Event with clear date
test2_data = {
    'url': 'https://example.com/pitch-night',
    'snippet': 'Monthly pitch night on January 15, 2026. 10 startups will present to investors.',
    'title': 'Startup Pitch Night - Bangalore'
}

# Test 3: Event with date range
test3_data = {
    'url': 'https://example.com/demo-day',
    'snippet': 'Demo Day happening from March 20-22, 2026. Applications open for seed-stage startups.',
    'title': 'Tech Startup Demo Day 2026'
}

# Test 4: Non-event content (should fail)
test4_data = {
    'url': 'https://example.com/article',
    'snippet': 'This is an article about fintech trends and market analysis.',
    'title': 'Fintech Market Analysis Report'
}

# Run tests
result1 = test_case("Original Error Case - No Dates", test1_data)
result2 = test_case("Event with Clear Date", test2_data)
result3 = test_case("Event with Date Range", test3_data)
result4 = test_case("Non-Event Content", test4_data)

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"Test 1 (No dates, has pitch keywords): {'PASS' if result1 else 'FAIL'}")
print(f"Test 2 (Clear date): {'PASS' if result2 else 'FAIL'}")
print(f"Test 3 (Date range): {'PASS' if result3 else 'FAIL'}")
print(f"Test 4 (Non-event): {'PASS' if not result4 else 'FAIL (should reject)'}")
