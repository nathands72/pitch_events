"""
Quick test to verify the parser can handle Tavily search results.
"""
from agents.parser_agent import ParserAgent

# Test data from the error message
test_data = {
    'url': 'https://www.linkedin.com/pulse/fintech-revolution-india-success-opportunities-sexbc',
    'snippet': "Karnataka's leadership in Fintech and its status as one of the largest tech hubs in the world makes it a prime location in India for future startups and Fintech firms.\n\nKarnataka has the ecosystems, sustainable infrastructure, consumer protection, competition, and financial stability to fully support and develop the Industry. Karnataka's Digital Payments Policy and Fintech Policy have additionally strengthened the state's ecosystems and infrastructure. [...] Diversified Landscape and Innovation Hub: Powered by cutting-edge technologies like AI and Big Data, Indian fintech offers a comprehensive range of solutions including payments, lending, insurance, and wealth management. Karnataka, a leading tech hub, provides an ideal investment environment with robust infrastructure, skilled talent, and supportive policies. [...] Various tier 2 and tier 3 cities are emerging as breakout hubs. Mangaluru, the Silicon Beach of India, is a hub of human capital and a resource-rich cluster and is likely to drive the way forward in Fintech. Its economic contribution to Karnataka is expected to rise up to around 17 per cent by 2030.",
    'title': "India's Fintech Boom: Trends, Challenges, and Opportunities"
}

# Test the parser
parser = ParserAgent()
result = parser.parse(test_data, source="tavily")

if result:
    print("[SUCCESS] Successfully parsed event!")
    print(f"  Title: {result.title}")
    print(f"  Description: {result.description[:100]}...")
    print(f"  Tags: {result.tags}")
    print(f"  Venue: {result.venue.type}")
else:
    print("[FAILED] Failed to parse event")

