import asyncio
import logging
import os

import database as db
import models
import scraper


class Handler:
    def __init__(self, country: str):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._db = db.FileClient(os.path.join(dir_path, "..", "data", country.lower()))
        self._all_jobs_scraper = scraper.AllJobsScraper(country)
        self._single_jobs_scraper = scraper.SingleJobScraper()

    async def run(self, keywords: str = "", *, until: int = -1):
        # await self._db.save_jobs(self._all_jobs_scraper.scrap_jobs(keywords, until=until))
        linkedin_job = models.LinkedInJob(
            **{
                "url":"https://de.linkedin.com/jobs/view/werkstudenten-b%C3%A4ckerei-m-w-d-im-verkauf-at-sehne-backwaren-kg-3847180297?position=3&pageNum=95&refId=bgcg3K4n6rjOiW3amevwUA%3D%3D&trackingId=skMHf2VCNnzZFZkr7yf%2Fyw%3D%3D&trk=public_jobs_jserp-result_search-card",
                "title":"Werkstudenten Bäckerei (m/w/d) im Verkauf",
                "company":{
                    "name":"Sehne Backwaren KG",
                    "url":"https://www.linkedin.com/company/sehne-backwaren-kg?trk=public_jobs_jserp-result_job-search-card-subtitle"
                },
                "location":{
                    "full_location":"Ehningen, Baden-Württemberg, Germany"
                },
                "posted_time":"2024-03-05"
            }
        )
        await self._single_jobs_scraper.scrap(linkedin_job)
        print(linkedin_job.json())


async def main():
    keywords_ = ""
    until_ = 86400
    location_ = "Munich"

    handler = Handler(location_)
    await handler.run(keywords_, until=until_)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    asyncio.run(main())
