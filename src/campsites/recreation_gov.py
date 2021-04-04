from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
import itertools
import json
import logging
import requests
from typing import Optional

from fake_useragent import UserAgent

logging.basicConfig(
    format="%(levelname)s\t%(asctime)s\t%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IS_AVAILABLE_KEYWORDS = ["Available"]
IS_NOT_AVAILABLE_KEYWORDS = ["Reserved", "Open", "Not Available"]

BASE_URL = "https://www.recreation.gov"
SEARCH_ENDPOINT = "/api/search"
AVAILABILITY_ENDPOINT = "/api/camps/availability/campground/"


@dataclass
class Campsite:
    availabilities: dict[str, str]
    campsite_id: str
    site: str
    type_of_use: str
    quantities: None
    min_num_people: int
    max_num_people: int
    loop: str
    capacity_rating: str
    campsite_type: str
    campsite_reserve_type: str

    def get_availabilities(self) -> list[datetime]:
        availabilities = []
        for date, availability in self.availabilities.items():
            if availability in IS_AVAILABLE_KEYWORDS:
                date = datetime.fromisoformat(date[:-1])
                availabilities.append(date)
        return availabilities


@dataclass
class AvailableSite:
    date: datetime
    campsite: Campsite

    def __lt__(self, other):
        return self.date < other.date

    def __hash__(self):
        return hash((self.date, self.campsite.site))


def make_get_request(url: str, params: dict[str, str]):
    headers = {"User-Agent": UserAgent().chrome}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Status code: {response.status_code}. Error: {response.text}")
    return json.loads(response.content)


def get_campground_id(query: str, url: str = f"{BASE_URL}{SEARCH_ENDPOINT}") -> str:
    params = {"q": query}
    campground_data = make_get_request(url, params)
    if "entity_id" not in campground_data:
        raise ValueError(f"Campground: {query} not found. Try being more specific.")
    campground_id = campground_data["entity_id"]
    logger.info(f"Found campground: {query} (campground id: {campground_id})")
    return campground_id


def get_campground_url(campground_id: str) -> str:
    return f"{BASE_URL}/camping/campgrounds/{campground_id}/availability"


def convert_date_to_string(date: datetime) -> str:
    # Recreation.gov is picky with date format - must be first day of month in ISO
    # format
    date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_format = date.isoformat() + ".000Z"
    return date_format


def get_campsites(campground_id: str, start_date: datetime) -> list[Campsite]:
    date_string = convert_date_to_string(start_date)
    params = {"start_date": date_string}
    url = f"{BASE_URL}{AVAILABILITY_ENDPOINT}{campground_id}/month?"
    # url = f"{BASE_URL}/camps/availability/campground/{campground_id}/month?"
    data = make_get_request(url, params)
    return [Campsite(**site) for site in data["campsites"].values()]


def get_all_available_campsites(
    campground_id: str, start_date: datetime
) -> list[AvailableSite]:
    campsites = get_campsites(campground_id, start_date)
    results = []
    for campsite in campsites:
        # We exclude picnic sites from the mix
        if campsite.type_of_use == "Day":
            continue
        availabilities = campsite.get_availabilities()
        if availabilities:
            for date in availabilities:
                results.append(AvailableSite(date, campsite))
    return results


def get_available_campsite_matching_criteria(
    campground_id: str,
    start_date: datetime,
    weekdays: list[str],
    nights: int,
    require_same_site: bool,
) -> list[AvailableSite]:
    all_available = get_all_available_campsites(campground_id, start_date)
    if require_same_site:
        available_sites = itertools.groupby(
            all_available, key=lambda x: x.campsite.site
        )
    else:
        available_sites = [("All", all_available)]
    passes_criteria = []
    for _, sites_available in available_sites:
        sites_available = sorted(sites_available)
        date_groups = itertools.groupby(sites_available, key=lambda x: x.date)
        # Filter by weekday unless weekday is not specified
        matches = [x for x, _ in date_groups if x.strftime("%A") in weekdays]
        for match_date in matches:
            all_nights_available = True
            available = []
            for _ in range(nights):
                night_availability = [
                    x for x in sites_available if x.date == match_date
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
