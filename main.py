#!/usr/bin/env python3
"""
MeasureCamp Calendar Scraper - Main Orchestrator

This script:
1. Scrapes the MeasureCamp calendar page for all events
2. Fetches details from each event's subdomain
3. Updates the local event database (events.json)
4. Generates an ICS calendar file (measurecamp-events.ics)
5. Returns exit code 0 if successful

Intended to be run daily via GitHub Actions.
"""

import sys
from datetime import datetime
from scraper import scrape_all_events
from event_manager import EventManager
from ics_generator import ICSGenerator


def main():
    print("=" * 60)
    print(f"MeasureCamp Calendar Scraper - {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        # Phase 1: Scrape events
        print("\n[1/3] Scraping MeasureCamp events...")
        scraped_events = scrape_all_events()

        if not scraped_events:
            print("WARNING: No events scraped!")
            return 1

        print(f"Successfully scraped {len(scraped_events)} events")

        # Phase 2: Update event database
        print("\n[2/3] Updating event database...")
        manager = EventManager('events.json')
        changed_ids = manager.update_events(scraped_events)
        manager.save_events()

        if changed_ids:
            print(f"Found {len(changed_ids)} new/updated events")
        else:
            print("No changes detected")

        # Phase 3: Generate ICS calendar
        print("\n[3/3] Generating ICS calendar file...")
        generator = ICSGenerator('events.json')
        success = generator.save_ics('measurecamp-events.ics')

        if not success:
            print("ERROR: Failed to generate ICS file")
            return 1

        # Summary
        print("\n" + "=" * 60)
        print(f" Scraping completed successfully")
        print(f"  - Total events in database: {len(manager.get_all_events())}")
        print(f"  - Future events: {len(manager.get_future_events())}")
        if changed_ids:
            print(f"  - Changed events: {len(changed_ids)}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
