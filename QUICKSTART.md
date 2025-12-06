# Quick Start Guide

## 1. Get API Keys

### Tavily (Required)
1. Go to https://tavily.com
2. Sign up for a free account
3. Get 1,000 free search credits
4. Copy your API key

### OpenAI (Required)
1. Go to https://platform.openai.com
2. Create an account or log in
3. Navigate to API keys
4. Create a new API key
5. Copy the key

## 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (for future scraping features)
playwright install
```

## 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# TAVILY_API_KEY=tvly-...
```

## 4. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## 5. Try a Search

1. Select your persona (Founder or Investor)
2. Enter a query like: "I'm a seed-stage fintech founder looking to pitch in San Francisco"
3. Set your date range (e.g., next 30 days)
4. Click "Search Events"

## Troubleshooting

**Error: "No module named 'tavily'"**
- Run: `pip install -r requirements.txt`

**Error: "Invalid API key"**
- Check your .env file has the correct keys
- Make sure there are no quotes around the keys

**No results found**
- Try a broader search query
- Expand your date range
- Remove location filter to search globally

**App won't start**
- Make sure you're in the project directory
- Check Python version: `python --version` (need 3.10+)
- Try: `streamlit run app.py --server.port 8502` (different port)

## Next Steps

- Save interesting events using the Save button
- Try different personas and filters
- Explore the match explanations to understand ranking
- Check the sidebar for saved events

Enjoy finding your perfect pitch event! 🎯
