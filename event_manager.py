import json
import os
from datetime import datetime
from pathlib import Path

class EventManager:
    def __init__(self, events_file='events.json'):
        self.events_file = events_file
        self.events = []
        self.load_events()

    def generate_event_id(self, city, date):
        """
        Generate unique event ID: city-slug-year
        Example: amsterdam-2026
        """
        city_slug = city.lower().replace(' ', '-').replace("'", '')
        year = date.split('-')[0] if date else 'unknown'
        return f"{city_slug}-{year}"

    def load_events(self):
        """Load existing events from JSON file."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    self.events = data.get('events', [])
                    print(f"Loaded {len(self.events)} existing events from {self.events_file}")
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.events_file}, starting fresh")
                self.events = []
        else:
            print(f"{self.events_file} not found, starting with empty event list")
            self.events = []

    def save_events(self):
        """Save events to JSON file."""
        with open(self.events_file, 'w') as f:
            json.dump({'events': self.events}, f, indent=2)
        print(f"Saved {len(self.events)} events to {self.events_file}")

    def find_event(self, event_id):
        """Find an event by ID in the stored events."""
        for event in self.events:
            if event.get('id') == event_id:
                return event
        return None

    def is_past_event(self, date_str):
        """Check if an event date is in the past."""
        if not date_str:
            return False
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d')
            return event_date < datetime.now()
        except ValueError:
            return False

    def update_events(self, scraped_events):
        """
        Compare scraped events with stored events.
        Update existing events, add new ones, and remove past events.
        Returns list of changed event IDs.
        """
        changed_ids = []

        # Create a set of IDs from scraped events for quick lookup
        scraped_ids = set()

        for scraped_event in scraped_events:
            event_id = self.generate_event_id(scraped_event['city'], scraped_event['date'])
            scraped_ids.add(event_id)

            stored_event = self.find_event(event_id)

            # Prepare new event data
            new_event_data = {
                'id': event_id,
                'city': scraped_event['city'],
                'url': scraped_event['url'],
                'date': scraped_event['date'],
                'time': scraped_event.get('time', '09:00'),
                'venue': scraped_event.get('venue'),
                'address': scraped_event.get('address'),
                'last_updated': datetime.now().isoformat() + 'Z'
            }

            if stored_event:
                # Check if anything changed
                changed = False
                for key in ['date', 'time', 'venue', 'address', 'url']:
                    if stored_event.get(key) != new_event_data[key]:
                        changed = True
                        break

                if changed:
                    print(f"Updating event: {event_id}")
                    stored_event.update(new_event_data)
                    changed_ids.append(event_id)
            else:
                # New event
                print(f"Adding new event: {event_id}")
                self.events.append(new_event_data)
                changed_ids.append(event_id)

        # Remove past events (optional - comment out if you want to keep history)
        # past_event_ids = []
        # for event in self.events:
        #     if self.is_past_event(event.get('date')):
        #         past_event_ids.append(event.get('id'))
        #
        # for past_id in past_event_ids:
        #     self.events = [e for e in self.events if e.get('id') != past_id]
        #     print(f"Removing past event: {past_id}")

        return changed_ids

    def get_all_events(self):
        """Return all stored events."""
        return self.events

    def get_future_events(self):
        """Return only future events."""
        return [e for e in self.events if not self.is_past_event(e.get('date'))]


if __name__ == "__main__":
    # Test the event manager
    manager = EventManager()

    # Simulate some scraped events
    test_events = [
        {
            'city': 'Amsterdam',
            'url': 'https://amsterdam.measurecamp.org',
            'date': '2026-04-18',
            'time': '09:00',
            'venue': 'House of Watt',
            'address': 'James Wattstraat 73, 1097 DL Amsterdam'
        },
        {
            'city': 'Malmo',
            'url': 'https://malmo.measurecamp.org',
            'date': '2026-01-17',
            'time': '09:00',
            'venue': 'Venue Name',
            'address': 'Some Address'
        }
    ]

    changed = manager.update_events(test_events)
    print(f"Changed events: {changed}")
    manager.save_events()
