# MeasureCamp Calendar Scraper

Automatically scrapes [MeasureCamp](https://www.measurecamp.org/) event information from around the world and generates a subscribable calendar (`.ics`) file.

## Features

- **Daily scraping** via GitHub Actions (runs at midnight UTC)
- **Persistent event database** (`events.json`) that tracks all events across years
- **Smart deduplication** - detects and updates changed event details
- **ICS calendar generation** - compatible with Google Calendar, Outlook, Apple Calendar, etc.
- **Public subscription** - users can subscribe with a simple raw GitHub URL
- **Scalable** - supports any number of events and years

## How It Works

1. **Scraper** fetches the MeasureCamp calendar page and extracts all event links
2. **Event Parser** visits each city's event page and extracts:
   - Date & time
   - Venue name
   - Address
   - Event URL
3. **Event Manager** compares with existing events:
   - Updates if details changed
   - Adds new events
   - Maintains history
4. **ICS Generator** creates a calendar file from all events
5. **Auto-Commit** pushes changes to GitHub (if any events changed)

## Subscribe to the Calendar

Add this URL to your calendar app:

```
https://raw.githubusercontent.com/braniq/measurecamp-calendar-scraper/main/measurecamp-events.ics
```

### Google Calendar
1. Open Google Calendar
2. Click **+ Create** → **Subscribe to calendar**
3. Paste the URL above
4. Click **Subscribe**

### Outlook / Apple Calendar
1. Open your calendar app
2. Look for "Import" or "Subscribe to Calendar"
3. Paste the URL above
4. Confirm

The calendar will automatically update daily as new events are added!

## Project Structure

```
├── main.py                    # Main orchestrator
├── scraper.py                 # Web scraping logic
├── event_manager.py           # Event deduplication & storage
├── ics_generator.py           # ICS file generation
├── events.json                # Persistent event database
├── measurecamp-events.ics     # Generated calendar file
├── requirements.txt           # Python dependencies
├── .github/workflows/
│   └── scrape-daily.yml       # GitHub Actions trigger
└── .gitignore
```

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py
```

This will:
1. Fetch all MeasureCamp events
2. Update `events.json`
3. Generate `measurecamp-events.ics`

## Files Generated

- **events.json**: JSON database of all scraped events with metadata
- **measurecamp-events.ics**: iCalendar file ready for calendar app import

## Data Format

Events are stored with the following structure:

```json
{
  "id": "amsterdam-2026",
  "city": "Amsterdam",
  "url": "https://amsterdam.measurecamp.org",
  "date": "2026-04-18",
  "time": "09:00",
  "venue": "House of Watt",
  "address": "Address details...",
  "last_updated": "2025-12-11T19:09:04.559546Z"
}
```

## Automation

The scraper runs automatically every day at **00:00 UTC** via GitHub Actions. You can also manually trigger it by:

1. Going to the **Actions** tab in GitHub
2. Selecting **Scrape MeasureCamp Events**
3. Clicking **Run workflow**

## Notes

- Events are identified by `{city}-{year}` to handle multiple events per city across different years
- Past events are kept in the database for historical purposes
- The scraper respectfully delays between requests to avoid overloading the website
- If an event page fails to parse, the scraper logs a warning but continues

## License

See [LICENSE](LICENSE) file for details.
