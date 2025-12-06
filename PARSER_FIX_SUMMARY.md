# Parser Agent Fix - Summary

## Issue
The `ParserAgent` was failing to parse events from Tavily search results when no explicit dates were found in the snippet, logging:
```
agents.parser_agent:_parse_snippet:258 - No dates found in snippet for: Startup Fundraising Summit - By Investors, For Founders
```

This caused valid pitch events to be rejected simply because their dates weren't in a recognizable format.

## Root Causes
1. **Limited date pattern matching**: The `_extract_dates_from_text` method only supported 3 basic date formats
2. **Strict rejection policy**: Events without dates were immediately rejected, even if they had strong event indicators (pitch keywords, summit, conference, etc.)
3. **EventSource validation error**: The `raw_data` field was being passed as a string instead of a dict

## Changes Made

### 1. Enhanced Date Extraction (`_extract_dates_from_text`)
**File**: `agents/parser_agent.py` (lines 384-461)

**Improvements**:
- Added support for 7 date formats (up from 3):
  - ISO format: `2025-12-06`
  - MM/DD/YYYY: `12/06/2025`
  - DD-MM-YYYY: `06-12-2025`
  - Month DD, YYYY: `January 15, 2026` or `Jan 15th, 2026`
  - DD Month YYYY: `15 January 2026` or `15th Jan 2026`
  - Month DD (no year): `January 15` or `Jan 15th`
  - DD Month (no year): `15 January` or `15th Jan`

- Added fuzzy parsing with `date_parser.parse(match, fuzzy=True)`
- Auto-corrects dates without years to current/next year
- Prevents duplicate date matches
- Added detailed debug logging to show:
  - Successfully extracted dates
  - Failed parse attempts
  - Text samples when no dates found

### 2. Lenient Snippet Parsing (`_parse_snippet`)
**File**: `agents/parser_agent.py` (lines 238-319)

**Improvements**:
- No longer rejects events without dates if they contain event indicators
- Checks for event-related keywords:
  - `summit`, `conference`, `event`, `meetup`, `demo day`
  - `pitch`, `competition`, `hackathon`, `workshop`
- For events without dates but with event indicators:
  - Creates event with default date (30 days from now)
  - Adds `date-uncertain` tag for manual verification
  - Appends warning to description: `[Date uncertain - please verify]`
  - Logs warning instead of silently rejecting

### 3. Fixed EventSource Validation (`_enrich_event`)
**File**: `agents/parser_agent.py` (lines 485-507)

**Fix**:
- Changed `raw_data` from string to dict to match schema requirements
- Now properly wraps snippet data in a dictionary with fields:
  - `snippet`: The search result snippet
  - `title`: The event title
  - `url`: The source URL

## Test Results

Created comprehensive test suite (`test_parser_comprehensive.py`) with 4 scenarios:

✅ **Test 1**: Event without dates but with pitch keywords → **PASS**
- Title: "Startup Fundraising Summit - By Investors, For Founders"
- Result: Created event with default date and `date-uncertain` tag

✅ **Test 2**: Event with clear date → **PASS**
- Title: "Startup Pitch Night - Bangalore"
- Date: "January 15, 2026"
- Result: Correctly extracted date

✅ **Test 3**: Event with date range → **PASS**
- Title: "Tech Startup Demo Day 2026"
- Date: "March 20-22, 2026"
- Result: Extracted start date

✅ **Test 4**: Non-event content → **PASS**
- Title: "Fintech Market Analysis Report"
- Result: Correctly rejected (no event indicators)

## Impact

### Before Fix
- Events without explicit dates were rejected
- Only 3 date formats supported
- No visibility into why parsing failed
- Validation errors when enriching events

### After Fix
- Events with pitch keywords are preserved even without dates
- 7+ date formats supported with fuzzy matching
- Detailed logging for debugging
- Proper schema validation
- Events tagged with `date-uncertain` for manual review

## Migration Notes

No breaking changes. Existing functionality is preserved and enhanced.

Events created without dates will have:
- `start_utc` and `end_utc` set to 30 days from parsing time
- `date-uncertain` tag in the tags list
- Warning appended to description

## Recommendations

1. **Manual Review**: Filter events with `date-uncertain` tag for manual verification
2. **URL Fetching**: Consider fetching full HTML from URLs for events without dates to extract more information
3. **NLP Enhancement**: Future improvement could use NLP/LLM to extract dates from natural language (e.g., "next week", "Q1 2026")
4. **Date Validation**: Add validation to ensure extracted dates are in the future (not past events)
