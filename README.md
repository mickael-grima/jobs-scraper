# jobs-scraper

This is a python module offering several jobs platform scrapers solutions

## LinkedIn

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
