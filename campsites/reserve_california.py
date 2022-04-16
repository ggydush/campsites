from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import requests
from typing import Any

from campsites.campsite import Campsite, AvailableCampsite
from campsites.common import make_get_request, make_post_request

logging.basicConfig(
    format="%(levelname)s\t%(asctime)s\t%(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://calirdr.usedirect.com"
SEARCH_ENDPOINT = "/rdr/rdr/fd/citypark/namecontains/"
PLACE_ENDPOINT = "/rdr/rdr/search/place"
AVAILABILITY_ENDPOINT = "/rdr/rdr/search/grid"
DATE_FORMAT = "%m-%d-%Y"
CAMPGROUND_URL = "https://www.reservecalifornia.com/"


@dataclass
class ReserveCaliforniaCampsite:
    Campground: str
    UnitId: int
    Name: str
    ShortName: str
    RecentPopups: int
    IsAda: bool
    AllowWebBooking: bool
    MapInfo: dict[str, Any]
    IsWebViewable: bool
    IsFiltered: bool
    UnitCategoryId: int
    SleepingUnitIds: list[int]
    UnitTypeGroupId: int
    UnitTypeId: int
    VehicleLength: int
    OrderBy: int
    OrderByRaw: int
    SliceCount: int
    AvailableCount: int
    Slices: dict[str, Any]

    def get_availabilities(self) -> list[datetime]:
        availabilities: list[datetime] = []
        for campsite in self.Slices.values():
            if campsite["IsFree"]:
                date_string = campsite["Date"]
                date = datetime.strptime(date_string, "%Y-%m-%d")
                availabilities.append(date)
        return availabilities

    def to_campsite(self) -> Campsite:
        return Campsite(campground=self.Campground, campsite=self.Name)


def get_campground_id(query: str, url: str = f"{BASE_URL}{SEARCH_ENDPOINT}") -> str:
    url_with_query = f"{url}{requests.utils.quote(query)}"  # type: ignore
    response = make_get_request(url_with_query)
    if not response:
        raise ValueError(f"Campground: {query} not found. Try being more specific.")
    top_hit = response[0]
    campground_name = top_hit["Name"]
    campground_id = top_hit["PlaceId"]
    logger.info(f"Found campground: {campground_name} (campground id: {campground_id})")
    return campground_id


def get_facility_ids(
    campground: str, url: str = f"{BASE_URL}{PLACE_ENDPOINT}"
) -> list[dict[str, str]]:
    campground_id = get_campground_id(campground)
    data = {
        "PlaceId": campground_id,
        "StartDate": datetime.today().strftime("%m-%d-%Y"),
    }
    response = make_post_request(url, data)
    if "SelectedPlace" not in response or response["SelectedPlace"] is None:
        raise ValueError(
            f"Could not find facilities in {campground} - try being more specific."
        )
    facilities = response["SelectedPlace"]["Facilities"]
    facility_ids: list[dict[str, str]] = []
    for facility in facilities.values():
        data = {
            "campground": facility["Name"],
            "facility_id": str(facility["FacilityId"]),
        }
        facility_ids.append(data)
    return sorted(facility_ids, key=lambda x: x.get("campground", ""))


def get_all_campsites(
    campground_id: str, start_date: datetime, months: int
) -> list[ReserveCaliforniaCampsite]:
    data = {
        "FacilityId": campground_id,
        "StartDate": start_date.strftime(DATE_FORMAT),
        "EndDate": (start_date + relativedelta(months=months)).strftime(DATE_FORMAT),
    }
    url = f"{BASE_URL}{AVAILABILITY_ENDPOINT}"
    response = make_post_request(url, data)
    campground = response["Facility"]["Name"]
    if not campground:
        raise ValueError(f"Could not find campground with ID: {campground_id}")
    logger.info(f"Found campground: {campground} (campground id: {campground_id})")
    campsites = response["Facility"]["Units"].values()
    results: list[ReserveCaliforniaCampsite] = []
    for site in campsites:
        site["Campground"] = campground
        results.append(ReserveCaliforniaCampsite(**site))
    return results


def rc_get_all_available_campsites(
    campground_id: str, start_date: datetime, months: int
) -> list[AvailableCampsite]:
    results: list[AvailableCampsite] = []
    campsites = get_all_campsites(
        campground_id=campground_id, start_date=start_date, months=months
    )
    for campsite in campsites:
        availabilities = campsite.get_availabilities()
        if availabilities:
            for date in availabilities:
                results.append(AvailableCampsite(date, campsite.to_campsite()))
    return results


def rc_get_campground_url(campground_id: str) -> str:
    return CAMPGROUND_URL
