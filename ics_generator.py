from icalendar import Calendar, Event
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os

class ICSGenerator:
    def __init__(self, events_file='events.json'):
        self.events_file = events_file
        self.events = []
        self.load_events()

    def load_events(self):
        """Load events from JSON file."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    self.events = data.get('events', [])
                    print(f"Loaded {len(self.events)} events for ICS generation")
            except json.JSONDecodeError as e:
                print(f"Error loading events file: {e}")
                self.events = []
        else:
            print(f"Events file not found: {self.events_file}")

    def create_calendar(self):
        """Create an iCalendar object with all events."""
        cal = Calendar()
        cal.add('prodid', '-//MeasureCamp Calendar Scraper//github.com/braniq//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'MeasureCamp Events')
        cal.add('x-wr-timezone', 'UTC')
        cal.add('x-wr-caldesc', 'MeasureCamp unconference events worldwide')
        cal.add('refresh-interval;value=duration', 'P1D')  # Refresh daily
        cal.add('color', '#A32638')  # MeasureCamp brand red

        for event_data in self.events:
            event = self.create_event(event_data)
            if event:
                cal.add_component(event)

        return cal

    def create_event(self, event_data):
        """Create an iCalendar Event from event data."""
        try:
            # Parse date and time
            date_str = event_data.get('date')
            time_str = event_data.get('time', '09:00')

            if not date_str:
                print(f"Warning: No date for event {event_data.get('id')}")
                return None

            # Combine date and time
            datetime_str = f"{date_str} {time_str}"
            event_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')

            # Set timezone to UTC (can be adjusted by calendar apps)
            event_datetime = event_datetime.replace(tzinfo=ZoneInfo('UTC'))

            # Create event
            event = Event()
            event.add('uid', f"{event_data.get('id')}@measurecamp.org")
            event.add('dtstamp', datetime.now(ZoneInfo('UTC')))
            event.add('dtstart', event_datetime)
            event.add('summary', f"MeasureCamp {event_data.get('city')}")
            event.add('description', f"MeasureCamp unconference in {event_data.get('city')}\n\nVenue: {event_data.get('venue', 'TBD')}\nAddress: {event_data.get('address', 'TBD')}\n\nMore info: {event_data.get('url')}")
            event.add('location', f"{event_data.get('venue', 'TBD')}, {event_data.get('address', 'TBD')}")
            event.add('url', event_data.get('url'))
            event.add('categories', 'conference,unconference,analytics,webanalytics,measurecamp')

            # Set event duration (assume 1 day event)
            from datetime import timedelta
            event.add('duration', timedelta(hours=8))

            # Mark as busy
            event.add('transp', 'OPAQUE')

            return event

        except Exception as e:
            print(f"Error creating event for {event_data.get('id')}: {e}")
            return None

    def save_ics(self, output_file='measurecamp-events.ics'):
        """Generate and save the ICS file."""
        cal = self.create_calendar()

        try:
            with open(output_file, 'wb') as f:
                f.write(cal.to_ical())
            print(f"Saved calendar to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving ICS file: {e}")
            return False


if __name__ == "__main__":
    generator = ICSGenerator()

    # If no events exist, create test events
    if not generator.events:
        print("No events found, creating test events...")
        test_events = {
            "events": [
                {
                    "id": "amsterdam-2026",
                    "city": "Amsterdam",
                    "url": "https://amsterdam.measurecamp.org",
                    "date": "2026-04-18",
                    "time": "09:00",
                    "venue": "House of Watt",
                    "address": "James Wattstraat 73, 1097 DL Amsterdam",
                    "last_updated": "2025-12-11T00:00:00Z"
                },
                {
                    "id": "malmo-2026",
                    "city": "Malmo",
                    "url": "https://malmo.measurecamp.org",
                    "date": "2026-01-17",
                    "time": "09:00",
                    "venue": "Test Venue",
                    "address": "Test Address",
                    "last_updated": "2025-12-11T00:00:00Z"
                }
            ]
        }
        with open('events.json', 'w') as f:
            json.dump(test_events, f, indent=2)
        generator.load_events()

    generator.save_ics()
