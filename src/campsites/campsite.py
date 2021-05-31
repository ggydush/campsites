from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass
import itertools
from typing import Optional


@dataclass
class Campsite:
    campground: str
    campsite: str


@dataclass
class AvailableCampsite:
    date: datetime
    campsite: Campsite

    def __lt__(self, other: AvailableCampsite) -> bool:
        return self.date < other.date

    def __hash__(self) -> int:
        return hash((self.date, self.campsite.campsite))


def filter_to_criteria(
    all_available: list[AvailableCampsite],
    weekdays: list[str],
    nights: int,
    require_same_site: bool,
    ignore: Optional[str] = None,
    calendar_date: Optional[datetime] = None,
    sub_campground: Optional[str] = None,
) -> list[AvailableCampsite]:
    if require_same_site:
        available_sites = [
            (x, list(y))
            for x, y in itertools.groupby(
                all_available, key=lambda x: x.campsite.campsite
            )
        ]
    else:
        available_sites = [("All", all_available)]
    passes_criteria: list[AvailableCampsite] = []
    for _, sites_available in available_sites:
        sites_available = sorted(sites_available)
        if sub_campground:
            sites_available = [
                x for x in sites_available if x.campsite.campground == sub_campground
            ]
        date_groups = itertools.groupby(sites_available, key=lambda x: x.date)
        if calendar_date:
            matches = [x for x, _ in date_groups if x.date() == calendar_date.date()]
        else:
            matches = [x for x, _ in date_groups if x.strftime("%A") in weekdays]
        for match_date in matches:
            all_nights_available = True
            available: list[AvailableCampsite] = []
            for _ in range(nights):
                night_availability = [
                    x
                    for x in sites_available
                    if x.date == match_date and x.campsite.campsite != ignore
                ]
                if not night_availability:
                    all_nights_available = False
                    break
                else:
                    available.extend(night_availability)
                match_date += timedelta(days=1)
            if all_nights_available:
                passes_criteria.extend(available)
    # Remove duplicates if there are any
    return list(set(passes_criteria))


def get_table_data(available_sites: list[AvailableCampsite]) -> list[dict[str, str]]:
    sorted_sites = sorted(available_sites, key=lambda x: (x.date, x.campsite.campsite))
    all_data: list[dict[str, str]] = []
    for available_site in sorted_sites:
        data = {
            "campground": available_site.campsite.campground,
            "campsite": available_site.campsite.campsite,
            "date": available_site.date.strftime("%m/%d/%y"),
            "weekday": available_site.date.strftime("%A"),
        }
        all_data.append(data)
    return all_data
