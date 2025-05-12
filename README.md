# Campsite availability via CLI

Small tool to check for campsite availability and send email notifications when
campsites become available.

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

  --notify                        Send email notification if campsite is available
  --calendar-date TEXT            Specific date to start reservation
                                  mm/dd/yyyy (can specify multiple)

  --sub-campground TEXT           Some campgrounds have sub-campgrounds that
                                  you can specify with this argument (can
                                  specify multiple)

  --help                          Show this message and exit.
```

Email notification support can be added by configuring the following environment
variables in a `.env` file in the project root, or adding them to your system
environment variables:

```
EMAIL_SMTP_SERVER="smtp.gmail.com"
EMAIL_SMTP_PORT="587"
EMAIL_USERNAME="your.email@gmail.com"
EMAIL_PASSWORD="your-app-password-or-email-password"
EMAIL_FROM="your.email@gmail.com"
EMAIL_TO="recipient.email@example.com"
```

If using Gmail, you'll likely need to use an App Password instead of your
regular password. See Google's guide on
[App Passwords](https://support.google.com/accounts/answer/185833) for more
information.

A sample configuration file is available in `.env.example` that you can copy and
modify.
