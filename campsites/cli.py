import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Callable, Set

import click

from campsites.campsite import filter_to_criteria, get_table_data
from campsites.messaging import send_message
from campsites.recreation_gov import (
    get_campground_id,
    rg_get_all_available_campsites,
    rg_get_campground_url,
)
from campsites.reserve_california import (
    get_facility_ids,
    rc_get_all_available_campsites,
    rc_get_campground_url,
)
import dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_table_string(data: list[dict[str, str]]) -> str:
    header = list(data[0].keys())
    values = [list(x.values()) for x in data]
    output = [header] + values
    tab_length = 4
    lengths = [max(len(str(x)) for x in line) + tab_length for line in zip(*output)]
    row_formatter = "".join(["{:" + str(x) + "s}" for x in lengths])
    table_string = "\n".join([row_formatter.format(*row) for row in output])
    return table_string


def create_log(
    table_data: list[dict[str, str]],
    campground_id: str,
    get_campground_url: Callable[[str], str],
) -> str:
    return (
        f"Reserve a spot here: {get_campground_url(campground_id)}\n"
        + f"Found Availability:\n\n{create_table_string(table_data)}...\n"
    )


def log_and_notify_error_message(
    message: str, error: str, check_every: int, notified_errors: defaultdict[str, int]
) -> None:
    date = str(datetime.now().date())
    error_message = (
        f"{message} Trying again in {check_every} minutes.\n"
        f"Error: {error}\n"
        f"Date: {date}"
    )
    logger.error(error_message)
    if error_message not in notified_errors:
        try:
            notified_errors[error_message] += 1
            # If 3 of the same errors are observed in the same day, send a notification.
            if notified_errors[error_message] >= 3:
                send_message(error_message)
        except Exception:
            pass


@click.option(
    "--sub-campground",
    type=str,
    help=(
        "Some campgrounds have sub-campgrounds that you can specify with this argument "
        + "(can specify multiple)"
    ),
    default=None,
    multiple=True,
)
@click.option(
    "--calendar-date",
    help="Specific date to start reservation mm/dd/yyyy (can specify multiple)",
    type=str,
    default=None,
    multiple=True,
)
@click.option(
    "--notify",
    is_flag=True,
    default=False,
    help="Send email notification if campsite is available",
)
@click.option(
    "--ignore",
    type=str,
    help="Specific campsite name to ignore (can specify multiple)",
    multiple=True,
)
@click.option(
    "--require-same-site",
    is_flag=True,
    default=False,
    help="Require campsite to be the same over all nights (no switching campsites)",
)
@click.option(
    "--check-every",
    help="Minutes to wait before checking again",
    type=int,
    default=5,
    show_default=True,
)
@click.option(
    "--api",
    help="Reservation API to use",
    default="recreation.gov",
    show_default=True,
    type=click.Choice(["recreation.gov", "reservecalifornia"]),
)
@click.option(
    "-m",
    "--months",
    help="Number of months to search",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "-d",
    "--day",
    help="Weekday of reservation start (can specify multiple) [default: all days]",
    multiple=True,
    default=[
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ],
    type=click.Choice(
        ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    ),
)
@click.option(
    "-n",
    "--nights",
    help="Number of nights to stay",
    default=1,
    type=int,
    show_default=True,
)
@click.option(
    "-c",
    "--campground",
    help="Name of campground to search for availability (can specify multiple)",
    type=str,
    multiple=True,
)
@click.command()
def main(
    campground: str,
    nights: int,
    day: list[str],
    require_same_site: bool,
    months: int,
    api: str,
    check_every: int,
    ignore: list[str],
    notify: bool,
    calendar_date: list[str],
    sub_campground: list[str],
) -> None:
    """Search for campsite availability from recreation.gov or reservecalifornia.

    Note: for `reservecalifornia`, campground argument must refer to the facility
    ID of the campsite. This is tricky to get from the website, so try using
    this tool but enter the park you are interested in as the campground.
    This should return a table of campsites and their associated facility ID.

    \b
    Examples:
    # Search for Kirby Cove and Hawk Campground for Friday or Saturday availability
    # this month
    find-campsites -c "Kirby Cove" -c "Hawk Campground" -d Friday -d Saturday
    # Search for facility IDs in Millerton Lake SRA
    find-campsites -c "Millerton Lake SRA" --api reservecalifornia
    # Search for specific campsite in Millerton Lake SRA
    find-campsites -c 1120 --api reservecalifornia
    """
    dotenv.load_dotenv("./.env.example")

    if nights < 1:
        raise ValueError("Nights must be greater than 1.")
    campgrounds = campground
    notified: defaultdict[str, Set] = defaultdict(set)
    notified_errors: defaultdict[str, int] = defaultdict(lambda: 0)
    while True:
        start_date = datetime.today()
        if calendar_date:
            dates = [datetime.strptime(x, "%m/%d/%Y") for x in calendar_date]  # type: ignore
        else:
            dates = []
        for campground in campgrounds:
            if api == "reservecalifornia":
                if not campground.isdigit():
                    logger.info(
                        "ReserveCalifornia must use facility ID. Searching for facility "
                        + "IDs using provided `campground_id` (note: this must be the "
                        + "park that the campground is in)"
                    )
                    facility_id_table = create_table_string(
                        get_facility_ids(campground)
                    )
                    logger.info(f"Found facilities in park:\n\n{facility_id_table}\n")
                    break

                get_campground_url = rc_get_campground_url
                get_all_available_campsites = rc_get_all_available_campsites
            else:
                get_campground_url = rg_get_campground_url
                get_all_available_campsites = rg_get_all_available_campsites
            try:
                campground_id = (
                    campground
                    if api == "reservecalifornia"
                    else get_campground_id(campground)
                )
                available = get_all_available_campsites(
                    campground_id=campground_id, start_date=start_date, months=months
                )
            except Exception as e:
                log_and_notify_error_message(
                    message="Failed to retrieve availability.",
                    error=str(e),
                    check_every=check_every,
                    notified_errors=notified_errors,
                )
                continue
            available = filter_to_criteria(
                available,
                weekdays=day,
                nights=nights,
                ignore=ignore,
                require_same_site=require_same_site,
                calendar_dates=dates,
                sub_campgrounds=sub_campground,
            )
            if available:
                table_data = get_table_data(available)
                log_message = create_log(table_data, campground_id, get_campground_url)
                logger.info(log_message)
                available_not_notified = [
                    x for x in available if hash(x) not in notified[campground]
                ]
                # Only notify if we have not sent a notification yet today
                if notify and available_not_notified:
                    # Keep email concise by limiting the table size
                    email_message = create_log(
                        table_data[0:2], campground_id, get_campground_url
                    )
                    try:
                        send_message(email_message)
                    except Exception as e:
                        log_and_notify_error_message(
                            message="Failed to retrieve availability.",
                            error=str(e),
                            check_every=check_every,
                            notified_errors=notified_errors,
                        )
                        continue
                    for x in available_not_notified:
                        notified[campground].add(hash(x))
            else:
                logger.info(
                    f"No availability found for {campground} :( "
                    f"Trying again in {check_every} minutes."
                )
        time.sleep(60 * check_every)


if __name__ == "__main__":
    main()
