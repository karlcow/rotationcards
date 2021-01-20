#!/usr/bin/env python

import datetime
import json
import os

import click
from dotenv import load_dotenv
import requests

load_dotenv()

OAUTH_TOKEN = os.getenv('OAUTH_TOKEN')
# this is the project ID for web-bugs rotation project
# see https://developer.github.com/v3/projects/
PROJECT_ID = os.getenv('PROJECT_ID')
# Python weekday
# Monday: 0 to Sunday: 6
# Saturday: 5, Sunday: 6 are not working days
# Add the forbidden days of the week.
COLUMNS = {
    '5301985': {'name': 'karl', 'avoid': 1},
    '5051659': {'name': 'dennis', 'avoid': None},
    '5051665': {'name': 'ksenia', 'avoid': None},
    '5051664': {'name': 'thomas', 'avoid': None},
}

HEADERS = {
    'Authorization': 'token {0}'.format(OAUTH_TOKEN),
    'Accept': 'application/vnd.github.inertia-preview+json',
    'User-Agent': 'miketaylr/rotationcards'
}

# GET /repos/:owner/:repo/projects -- this gets the project ID
# curl -H "Accept: application/vnd.github.inertia-preview+json" -H "Authorization: token OAUTH_TOKEN_HERE" https://api.github.com/repos/miketaylr/test/projects
# to get the ID, then we have to get column keys from that.
# curl -H "Accept: application/vnd.github.inertia-preview+json" -H "Authorization: token OAUTH_TOKEN_HERE" https://api.github.com/projects/4032465/columns

@click.command()
@click.option('--firstdate', prompt='The first weekday to start with',
              help='The first weekday to start with. Format: YYYY-MM-DD')
def make_cards(firstdate):
    """
    Create rotation cards starting at a specific date.

    rotations: 2 is the default.
    The rotations is the number of times one individual will do rotations.
    """
    click.echo("OK, making cards starting with {0}".format(firstdate))
    days_cards = create_rotation_days(firstdate, rotations=2)
    for card in days_cards:
        create_card(card)


def create_rotation_days(firstdate, rotations):
    """
    Create a list of rotation days to create as card.

    The format is:
    [(person_name, column_id, day_1, day_2), …]
    """
    days_card = []
    start_date = get_start_date(firstdate)
    working_days = build_workdays(start_date, rotations)
    while working_days:
        for person in COLUMNS:
            # First day
            first_day = working_days[0]
            if first_day.weekday() == COLUMNS[person]['avoid']:
                first_day = working_days[1]
                working_days.pop(1)
                next_day = working_days[1]
                working_days.pop(1)
            else:
                working_days.pop(0)
                next_day = working_days[0]
                working_days.pop(0)
            card = (COLUMNS[person]['name'], person, first_day, next_day)
            days_card.append(card)
    return days_card


def get_start_date(firstdate):
    """Return the first date."""
    try:
        day = datetime.datetime.strptime(firstdate, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect firstdate format, should be YYYY-MM-DD")
    return day


def build_workdays(start_date, rotations):
    """Return a list of days for the number of rotation next valid day."""
    # How many participants, 2 days by participants, nb of rotations
    nb_days = len(COLUMNS) * 2 * rotations
    day_counter = nb_days - 1
    day = start_date
    business_days = [start_date]
    while day_counter > 0:
        gap = nb_days - day_counter
        day = get_next_workday(day)
        business_days.append(day)
        day_counter -= 1
    return business_days


def get_next_workday(day):
    """Get the next valid day of work."""
    if day.weekday() == 4:
        # Friday
        next_day = day + datetime.timedelta(days=3)
    else:
        next_day = day + datetime.timedelta(days=1)
    return next_day


def create_card(card):
    """Make the GitHub request to create the card.
    POST /projects/columns/:column_id/cards
    params: note (string)
    """
    name, column_id, day_1, day_2 = card
    day_1_str = day_1.strftime('%a, %b %d')
    day_2_str = day_2.strftime('%a, %b %d')
    full_body = f"* [ ] {day_1_str}\n* [ ] {day_2_str}"
    uri = 'https://api.github.com/projects/columns/{0}/cards'.format(
        column_id)
    rv = requests.post(uri, data=json.dumps(
        {"note": full_body}), headers=HEADERS)
    click.echo(rv.status_code)


if __name__ == '__main__':
    make_cards()
