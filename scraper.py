import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from urllib.parse import urlparse

def get_calendar_events():
    """
    Fetch the main calendar page and extract all event links.
    Returns a list of tuples: (city_name, event_url)
    """
    calendar_url = "https://www.measurecamp.org/measurecamp-calendar/"

    try:
        response = requests.get(calendar_url, timeout=10)
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
        response = requests.get(event_url, timeout=10)
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

    # Look for header section with event details
    # Pattern: date and time in one h3/span, venue in another h3/span
    headers = soup.find_all(['h3', 'span'])

    date_str = None
    time_str = None
    venue_str = None
    address_str = None

    for i, elem in enumerate(headers):
        text = elem.get_text(strip=True)

        # Match date pattern: "Saturday 18 Apr, 2026" or "Saturday 18 Apr"
        date_match = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+(\w+),?\s*(\d{4})?', text)
        if date_match:
            day_name, day, month, year = date_match.groups()
            date_str = f"{day_name} {day} {month}" + (f" {year}" if year else "")

        # Match time pattern: "Starting at 09:00" or "09:00"
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match and not date_match:  # Make sure it's not part of date
            time_str = f"{time_match.group(1)}:{time_match.group(2)}"

        # Look for venue (usually before address)
        # Heuristic: if it's not a date/time, might be venue or address
        if not date_match and not time_match and text and len(text) < 100:
            if address_str and not venue_str:
                venue_str = text
            elif not address_str and not venue_str:
                # Could be venue name
                if ',' not in text:  # Venue names usually don't have commas
                    venue_str = text

    # Try alternative extraction method - look for specific patterns in text content
    page_text = soup.get_text()

    # Try to find date in page text
    if not date_str:
        date_match = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+(\w+),?\s*(\d{4})?', page_text)
        if date_match:
            day_name, day, month, year = date_match.groups()
            date_str = f"{day_name} {day} {month}" + (f" {year}" if year else "")

    # Try to find time in page text
    if not time_str:
        time_match = re.search(r'[Ss]tarting at\s+(\d{1,2}):(\d{2})', page_text)
        if time_match:
            time_str = f"{time_match.group(1)}:{time_match.group(2)}"

    # Look for venue and address in structured way
    # Usually in format: venue name on one line, address on next
    for elem in soup.find_all(['h3', 'p', 'div']):
        text = elem.get_text(strip=True)

        # Check if it looks like an address (contains number, street indicators, etc.)
        if re.search(r'\d+.*(?:street|str|avenue|ave|road|rd|lane|ln|square|sq|plaza|drive|dr|court|ct|building|floor|apartment|apt|suite)', text, re.IGNORECASE):
            address_str = text
        elif venue_str and not address_str and ',' in text and any(x in text for x in ['street', 'str', 'avenue', 'ave', 'road', 'rd', 'lane', 'ln', 'square', 'plaza', 'drive', 'dr', 'court', 'ct']):
            address_str = text

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
