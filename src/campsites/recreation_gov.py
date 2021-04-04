from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

from campsites.campsite import Campsite, AvailableCampsite
from campsites.common import make_get_request


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
class RecreationGovCampsite:
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

    def to_campsite(self) -> Campsite:
        return Campsite(campground=self.loop, campsite=self.site)


def get_campground_id(query: str, url: str = f"{BASE_URL}{SEARCH_ENDPOINT}") -> str:
    params = {"q": query}
    campground_data = make_get_request(url, params)
    if "entity_id" not in campground_data:
        raise ValueError(f"Campground: {query} not found. Try being more specific.")
    campground_id = campground_data["entity_id"]
    logger.info(f"Found campground: {query} (campground id: {campground_id})")
    return campground_id


def rg_get_campground_url(campground_id: str) -> str:
    return f"{BASE_URL}/camping/campgrounds/{campground_id}/availability"


def convert_date_to_string(date: datetime) -> str:
    # Recreation.gov is picky with date format - must be first day of month in ISO
    # format
    date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_format = date.isoformat() + ".000Z"
    return date_format


def get_all_campsites(
    campground_id: str,
    start_date: datetime,
    months: int,
) -> list[RecreationGovCampsite]:
    all_sites = []
    for _ in range(months):
        date_string = convert_date_to_string(start_date)
        params = {"start_date": date_string}
        url = f"{BASE_URL}{AVAILABILITY_ENDPOINT}{campground_id}/month?"
        # url = f"{BASE_URL}/camps/availability/campground/{campground_id}/month?"
        data = make_get_request(url, params)
        all_sites.extend(
            [RecreationGovCampsite(**site) for site in data["campsites"].values()]
        )
        start_date = start_date + relativedelta(months=1)
    return all_sites


def rg_get_all_available_campsites(
    campground_id: str, start_date: datetime, months: int
) -> list[AvailableCampsite]:
    results = []
    campsites = get_all_campsites(
        campground_id=campground_id, start_date=start_date, months=months
    )
    for campsite in campsites:
        # We exclude picnic sites from the mix
        if campsite.type_of_use == "Day":
            continue
        availabilities = campsite.get_availabilities()
        if availabilities:
            for date in availabilities:
                results.append(AvailableCampsite(date, campsite.to_campsite()))
    return results
