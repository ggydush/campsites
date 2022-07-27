# Campsite availability via CLI

Installation:
```
git clone https://github.com/ggydush/campsites.git
cd campsites 
poetry install
```
Requires python 3.9. If you don't have python3, here are some suggested steps:

1. install python 3.9 here: https://www.python.org/downloads/release/python-390/
2. install pip https://phoenixnap.com/kb/install-pip-mac
3. `git clone https://github.com/ggydush/campsites.git`
4. `cd campsites`
5. create virtual enviroment: `python3 -m venv venv3.9campsites`
6. activate venv: `source venv3.9campsites/bin/activate`
7. install poetry: `pip3 install poetry`
8. install the campsites package: `poetry install`
9. `find-campsites --help` or `poetry run find-campsites`

You can still use with other python versions (like 3.7), but you  need to adapt the code. See [issue 3](https://github.com/ggydush/campsites/issues/3).

# Usage
Small tool to check for campsite availability and notify via text message using Twilio.

```
▶ find-campsites --help
Usage: find-campsites [OPTIONS]

  Search for campsite availability from recreation.gov or reservecalifornia.

  Note: for `reservecalifornia`, campground argument must refer to the
  facility ID of the campsite. This is tricky to get from the website, so
  try using this tool but enter the park you are interested in as the
  campground. This should return a table of campsites and their associated
  facility ID.

  Examples:
  # Search for Kirby Cove and Hawk Campground for Friday or Saturday availability
  # this month
  find-campsites -c "Kirby Cove" -c "Hawk Campground" -d Friday -d Saturday
  # Search for facility IDs in Millerton Lake SRA
  find-campsites -c "Millerton Lake SRA" --api reservecalifornia
  # Search for specific campsite in Millerton Lake SRA
  find-campsites -c 1120 --api reservecalifornia

Options:
  -c, --campground TEXT           Name of campground to search for
                                  availability (can specify multiple)

  -n, --nights INTEGER            Number of nights to stay  [default: 1]
  -d, --day [Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday]
                                  Weekday of reservation start (can specify
                                  multiple) [default: all days]

  -m, --months INTEGER            Number of months to search  [default: 1]
  --api [recreation.gov|reservecalifornia]
                                  Reservation API to use  [default:
                                  recreation.gov]

  --check-every INTEGER           Minutes to wait before checking again
                                  [default: 5]

  --require-same-site             Require campsite to be the same over all
                                  nights (no switching campsites)

  --ignore TEXT                   Specific campsite name to ignore (can
                                  specify multiple)

  --notify                        Send text message if campsite is available
  --calendar-date TEXT            Specific date to start reservation
                                  mm/dd/yyyy (can specify multiple)

  --sub-campground TEXT           Some campgrounds have sub-campgrounds that
                                  you can specify with this argument (can
                                  specify multiple)

  --help                          Show this message and exit.
  ```

Text message support can be added by creating a Twilio account and adding the following to either a `.env` file in the project root, or adding to environment variables.

```
TWILIO_ACCOUNT_SID="YOUR_TWILIO_SID"
TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH"
TWILIO_FROM_NUMBER="YOUR_TWILIO_NUMBER"
TWILIO_TO_NUMBER = "YOUR_PHONE_NUMBER"
```

# Finding Campsites
Enter the name of the campground as it appears on https://www.reservecalifornia.com/Web/ and `find-campsites` will return a table of facilities. Then use that facility id to search for availability. The other way to find the campsite ID is in the URL after getting deep into the booking. For Big Basin Redwoods, which ahs campground id of 3, the facility_id could be 333 for Seqouia group. See https://www.reservecalifornia.com/Web/#!park/3/333 to compare.

```
❯ find-campsites -c "Big Basin Redwoods SP" --api reservecalifornia
INFO	2022-07-26 22:04:38,880	ReserveCalifornia must use facility ID. Searching for facility IDs using provided `campground_id` (note: this must be the park that the campground is in)
INFO	2022-07-26 22:04:39,158	Found campground: Big Basin Redwoods SP (campground id: 3)
INFO	2022-07-26 22:04:39,375	Found facilities in park:

campground                                 facility_id
Huckleberry Campground (sites 42-75)       336
Lower Blooms Creek (sites 103-138)         332
Sempervirens Campground (sites 157-188)    335
Sequoia Group 1 & 2                        333
Sky Meadow Group 1 & 2                     338
Upper Blooms Creek (sites 139-156)         339
Wastahi Campground (sites 76-102)          337

<ctrl+c> to exit
❯ find-campsites -c 336 --api reservecalifornia
INFO	2022-07-26 22:05:50,679	Found campground: Huckleberry Campground (sites 42-75) (campground id: 336)
INFO	2022-07-26 22:05:50,680	No availability found for 336 :( Trying again in 5 minutes.
```
