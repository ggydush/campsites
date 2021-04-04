from datetime import datetime
import logging
import time

import click


from campsites.messaging import send_message
from campsites.recreation_gov import (
    get_campground_id,
    get_campground_url,
    get_available_campsite_matching_criteria,
    AvailableSite,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_table_data(available_sites: list[AvailableSite]):
    sorted_sites = sorted(available_sites, key=lambda x: (x.date, x.campsite.site))
    all_data = []
    for available_site in sorted_sites:
        data = {
            "loop": available_site.campsite.loop,
            "site": available_site.campsite.site,
            "date": available_site.date.strftime("%m/%d/%y"),
            "weekday": available_site.date.strftime("%A"),
        }
        all_data.append(data)
    return all_data


def create_table_string(data: list[dict[str, str]]):
    header = list(data[0].keys())
    values = [list(x.values()) for x in data]
    output = [header] + values
    tab_length = 4
    lengths = [max(len(str(x)) for x in line) + tab_length for line in zip(*output)]
    row_formatter = "".join(["{:" + str(x) + "s}" for x in lengths])
    output_str = "\n".join([row_formatter.format(*row) for row in output])
    return output_str


@click.option(
    "--notify",
    is_flag=True,
    default=False,
    help="Send text message if campsite is available",
)
@click.option(
    "--require_same_site",
    is_flag=True,
    default=False,
    help="Require campsite to be the same over all nights (no switching campsites)",
)
@click.option(
    "--check_every",
    help="Minutes to wait before checking again",
    type=int,
    default=60,
    show_default=True,
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
    "-c", "--campground", help="Name of campground to search for availability", type=str
)
@click.command()
def main(campground, nights, day, require_same_site, months, check_every, notify):
    """Search for campsite availability from recreation.gov."""
    if nights < 1:
        raise ValueError("Nights must be greater than 1.")
    while True:
        notified = False
        start_date = datetime.today()
        campground_id = get_campground_id(campground)
        all_results = []
        for months in range(months):
            results = get_available_campsite_matching_criteria(
                campground_id=campground_id,
                start_date=start_date,
                weekdays=day,
                nights=nights,
                require_same_site=require_same_site,
            )
            all_results.extend(results)
            start_date = start_date.replace(month=start_date.month + 1)
        if all_results:
            table_data = get_table_data(all_results)
            short_table_data = table_data[0:2]
            log_message = (
                f"Found Availability:\n\n{create_table_string(table_data)}\n"
                + f"Reserve a spot here: {get_campground_url(campground_id)}"
            )
            logger.info(log_message)
            if notify and not notified:
                text_message = (
                    f"Found Availability:\n\n{create_table_string(short_table_data)}\n"
                    + f"Reserve a spot here: {get_campground_url(campground_id)}"
                )
                send_message(text_message)
                notified = True
        else:
            logger.info(
                f"No availability found :( trying again in {check_every} minutes"
            )
        time.sleep(60 * check_every)


if __name__ == "__main__":
    main()
