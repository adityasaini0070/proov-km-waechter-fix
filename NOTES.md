# What I checked, and what the agent got wrong

Write this yourself, in your own words. It is the part of the repo that proves the work is yours.

## What the agent got wrong
When tasked with sweeping the helper files for quiet bugs, the agent initially didn't spot the inverted conversion constant in `fleet_utils.py`. `MILES_PER_KM` was incorrectly set to `1.609` (which is actually km-per-mile), making the miles calculation ~2.59x too large. I had to explicitly catch this during the code review to ensure the English partner garage receives the correct fleet distance.

## What I checked before I accepted its work
I ran `pytest` to verify that all edge cases (such as missing `last_service_km` values) no longer crash the scripts and correctly default to the odometer reading. I also checked `km_wachter.py` to ensure the core business rules — the 15,000 km service interval and the 80% warning threshold — remained strictly untouched. Finally, I executed `verify.py` manually to validate all acceptance criteria before marking the work as complete.

## What the data actually said
Despite the intuitive assumption that older cars or cars with higher total mileage break down more often, the data showed that total distance driven (`odometer_km`) and vehicle age (`age_years`) had near-zero correlation with breakdowns. Instead, the strongest predictors of a breakdown were the kilometers driven since the last service (`km_since_service`), followed by average daily usage (`avg_daily_km`) and vehicle load factor (`load_factor`).
