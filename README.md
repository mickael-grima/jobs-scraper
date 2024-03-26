# jobs-scraper

This is a python module offering several jobs platform scrapers solutions

## Installation

Clone this project, and:

```commandline
pip install .
```

## Supported Jobs Platforms

### LinkedIn

This sub-module takes care of:
- fetching all jobs from the LinkedIn search page, with the function `scrap_all_jobs`
- scraping all job's details for a previously fetched job, with the async function `scrap_single_job`

```python
import asyncio
from jobsscraper import linkedin

location = "Garmisch"
keyword = "Python"


async def run():
    # get all linkedin jobs
    all_jobs = list(linkedin.scrap_all_jobs(location, keyword=keyword))

    my_job = all_jobs[0]
    await linkedin.scrap_single_job(my_job)

    print(my_job)


if __name__ == "__main__":
    asyncio.run(run())
```

#### Debugging

In case the script is not working as expected, you have several way to debug it:
- check the logs of course
- pass the key-argument `headless=False` to the `scrap_all_jobs` method.
This will open the Browser's interface, and you will be able to follow the different
scraping steps
- export the environment variable `LINKEDIN_SCREENSHOT_ON_ERROR=1` before running
your script. It will take a screenshot of the last browser's page before the error
is raised, if any.

```commandline
export LINKEDIN_SCREENSHOT_ON_ERROR=1
```

```python
all_jobs = list(linkedin.scrap_all_jobs(location, keyword=keyword, headless=False))
```
