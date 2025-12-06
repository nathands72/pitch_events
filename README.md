# Realtime Startup Pitch Event Finder

A Streamlit web application that finds real-time startup pitch events for founders and investors using AI-powered search, multi-agent orchestration, and RAG.

## 🎯 Features

- **Real-time Search**: Uses Tavily API for fresh web search results
- **Multi-Platform Aggregation**: Searches across Eventbrite, Meetup, Luma, and more
- **Smart Matching**: AI-powered ranking based on semantic similarity, recency, location, and pitch slot availability
- **Pitch Slot Detection**: Automatically identifies events with pitch opportunities
- **Vector Database**: Stores canonical events with embeddings for fast retrieval
- **RAG Assistant**: Conversational interface for event discovery (coming soon)

## 🏗️ Architecture

### Multi-Agent System

1. **SearchAgent**: Real-time web search via Tavily + platform APIs
2. **FetcherAgent**: Content retrieval with Playwright (coming soon)
3. **ParserAgent**: Extract and normalize event data from HTML/JSON
4. **DeduperAgent**: Canonicalize duplicate events (coming soon)
5. **EmbedderAgent**: Generate embeddings and summaries
6. **RankerAgent**: Multi-factor scoring and ranking
7. **ActionAgent**: Automation and prefill (coming soon)
8. **AssistantAgent**: RAG conversational interface (coming soon)

### Tech Stack

- **Frontend**: Streamlit
- **Search**: Tavily API
- **Vector DB**: Chroma (with support for Pinecone, Weaviate)
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: GPT-4 Turbo
- **Web Scraping**: Playwright + BeautifulSoup

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key
- Tavily API key (get 1,000 free credits at https://tavily.com)

### Installation

1. Clone the repository:
```bash
cd pitch_events
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers (for web scraping):
```bash
playwright install
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage

1. **Select your persona**: Founder or Investor
2. **Enter your intent**: e.g., "I'm a seed-stage fintech founder looking to pitch in Bangalore"
3. **Set filters**: Date range, location, industry, price, etc.
4. **Search**: Click "Search Events" to find matching events
5. **Review results**: Browse ranked events with match scores and explanations
6. **Take action**: Register, apply to pitch, save events, or contact organizers

## 🗂️ Project Structure

```
pitch_events/
├── app.py                  # Streamlit application
├── agents/                 # Multi-agent system
│   ├── search_agent.py     # Tavily + platform API search
│   ├── parser_agent.py     # Event extraction & normalization
│   ├── embedder_agent.py   # Embedding generation
│   └── ranker_agent.py     # Scoring & ranking
├── models/                 # Data models
│   └── event_schema.py     # Pydantic schemas
├── utils/                  # Utilities
│   ├── config.py           # Configuration management
│   └── vector_db.py        # Vector database abstraction
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## 🔧 Configuration

Edit `.env` to configure:

- **API Keys**: OpenAI, Tavily, Eventbrite, Meetup
- **Vector DB**: Choose between Chroma (local), Pinecone, or Weaviate
- **Models**: Embedding model, LLM model
- **Search**: Max results, cache TTL

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

## 📝 Canonical Event Schema

Events are normalized into a canonical schema:

```json
{
  "event_id": "uuid",
  "title": "Startup Pitch Night — Bangalore",
  "description": "...",
  "start_utc": "2026-01-20T14:00:00Z",
  "venue": {
    "type": "in-person",
    "city": "Bangalore"
  },
  "pitch_slots": {
    "available": true,
    "slot_count": 10,
    "application_deadline": "2026-01-01"
  },
  "registration": {
    "type": "ticket",
    "url": "https://...",
    "price": 0
  },
  "tags": ["seed", "fintech", "demo-day"]
}
```

## 🎯 Roadmap

- [x] MVP: Search, parse, rank events
- [ ] FetcherAgent with Playwright
- [ ] DeduperAgent for canonical merging
- [ ] RAG Assistant for conversational search
- [ ] ActionAgent for registration automation
- [ ] Background re-check for saved events
- [ ] Email notifications for new matches
- [ ] Platform API integrations (Eventbrite, Meetup)

## 📚 Resources

- [Tavily Documentation](https://docs.tavily.com)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Chroma Documentation](https://docs.trychroma.com)

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

**Built with ❤️ using Tavily, OpenAI, and Streamlit**
