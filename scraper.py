import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from urllib.parse import urlparse

# Headers to mimic a browser request
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def get_calendar_events():
    """
    Fetch the main calendar page and extract all event links.
    Returns a list of tuples: (city_name, event_url)
    """
    calendar_url = "https://www.measurecamp.org/measurecamp-calendar/"

    try:
        response = requests.get(calendar_url, headers=BROWSER_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching calendar page: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the pagecontents div and extract event links
    events = []

    # Look for all links that point to event subdomains
    for link in soup.find_all('a', href=True):
        href = link['href']

        # Match measurecamp subdomains (e.g., amsterdam.measurecamp.org)
        if 'measurecamp.org' in href and not href.startswith('https://www.measurecamp.org'):
            # Extract city name from text
            text = link.get_text(strip=True)

            # Parse format like "17th Jan – Malmo" or "17th Jan – Malmo (note)"
            match = re.search(r'–\s*(.+?)(?:\s*\(|$)', text)
            if match:
                city = match.group(1).strip()
                events.append({
                    'city': city,
                    'url': href if href.startswith('http') else 'https:' + href if href.startswith('//') else 'https://' + href,
                    'raw_text': text
                })

    return events


def extract_event_details(event_url):
    """
    Fetch an individual event page and extract:
    - Date (parsed into YYYY-MM-DD format)
    - Time (HH:MM format)
    - Venue name
    - Full address
    """
    try:
        response = requests.get(event_url, headers=BROWSER_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching event page {event_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    details = {
        'url': event_url,
        'date': None,
        'time': None,
        'venue': None,
        'address': None
    }

    date_str = None
    time_str = None
    venue_str = None
    address_str = None

    # First, look for the structured header with date in class="headerdetails datey"
    header_details = soup.find('div', class_='headerdetails datey')
    if header_details:
        # Date is in h3 within headerdate div
        header_date = header_details.find('div', class_='headerdate')
        if header_date:
            h3 = header_date.find('h3')
            if h3:
                # Extract date from h3 text (e.g., "Saturday 14 Jun, 2025")
                text = h3.get_text(strip=True)
                # Remove icon text if present
                text = re.sub(r'<i.*?</i>', '', text)
                text = h3.get_text(strip=True)
                date_match = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+(\w+),?\s*(\d{4})?', text)
                if date_match:
                    day_name, day, month, year = date_match.groups()
                    date_str = f"{day_name} {day} {month}" + (f" {year}" if year else "")

            # Time info might be in span (e.g., "- 8h30 - 17h00 + after")
            # We'll treat as all-day event if time is not clearly specified
            span = header_date.find('span')
            if span:
                span_text = span.get_text(strip=True)
                # Try to extract specific time patterns (e.g., "09:00" or "8h30")
                time_match = re.search(r'(\d{1,2}):(\d{2})', span_text)
                if time_match:
                    time_str = f"{time_match.group(1)}:{time_match.group(2)}"

    # Look for venue and address in structured "headerdetails locy" container
    header_loc = soup.find('div', class_='headerdetails locy')
    if header_loc:
        # Venue name is in h3 within headerloc div
        header_loc_div = header_loc.find('div', class_='headerloc')
        if header_loc_div:
            h3 = header_loc_div.find('h3')
            if h3:
                # Get text from h3, excluding icon
                venue_str = h3.get_text(strip=True)

            # Address is in span, need to remove the link text
            span = header_loc_div.find('span')
            if span:
                span_text = span.get_text(strip=True)
                # Remove link text like "Localisation", "Map", etc.
                address_str = re.sub(r'\s*\(?(?:Localisation|Localiser|View the venue|Maps?|Localizer).*$', '', span_text, flags=re.IGNORECASE).strip()

    # Parse date to YYYY-MM-DD format
    parsed_date = None
    if date_str:
        try:
            # Try parsing with year (format: "Saturday 17 Jan 2026")
            dt = datetime.strptime(date_str, "%A %d %b %Y")
            parsed_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                # Try parsing without year (format: "Saturday 17 Jan")
                dt = datetime.strptime(date_str, "%A %d %b")
                # Infer year: if month is before current month, use next year; else use current year
                today = datetime.now()
                year = today.year
                if dt.month < today.month:
                    year += 1
                dt = dt.replace(year=year)
                parsed_date = dt.strftime("%Y-%m-%d")
            except ValueError as e:
                print(f"Could not parse date '{date_str}': {e}")

    details['date'] = parsed_date
    details['time'] = time_str or "09:00"  # Default to 9 AM if not found
    details['venue'] = venue_str
    details['address'] = address_str

    return details


def scrape_all_events():
    """
    Main scraping function: get calendar events, then fetch details for each.
    Returns a list of event dictionaries.
    """
    print("Fetching calendar page...")
    calendar_events = get_calendar_events()
    print(f"Found {len(calendar_events)} event links")

    all_events = []

    for i, event in enumerate(calendar_events):
        print(f"Scraping {i+1}/{len(calendar_events)}: {event['city']} ({event['url']})")

        details = extract_event_details(event['url'])
        if details and details['date']:
            event.update(details)
            all_events.append(event)
        else:
            print(f"  - Warning: Could not extract details for {event['city']}")

        # Rate limiting - be respectful to the server
        time.sleep(1)

    return all_events


if __name__ == "__main__":
    events = scrape_all_events()
    for event in events:
        print(f"\n{event['city']}:")
        print(f"  Date: {event['date']}")
        print(f"  Time: {event['time']}")
        print(f"  Venue: {event['venue']}")
        print(f"  Address: {event['address']}")
