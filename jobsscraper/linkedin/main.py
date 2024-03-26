from typing import Iterator

from . import models
from .scraper import AllJobsScraper, SingleJobScraper


def scrap_all_jobs(
        location: str,
        *,
        keyword: str = "",
        until: int = 86400,
        headless: bool = True
) -> Iterator[models.LinkedInJob]:
    """
    Navigate the LinkedIn search Webpage and extract all found jobs
    """
    scraper = AllJobsScraper(location, headless=headless)
    return scraper.scrap_jobs(keywords=keyword, until=until)


single_job_scraper: SingleJobScraper | None = None


async def scrap_single_job(data: models.LinkedInJob) -> None:
    """
    data provides a url with more details about this linkedin job
    this method scrap this url's webpage, and enhance the given
    data model with the extracted data
    """
    global single_job_scraper
    # Construct the scraper if not done once
    if single_job_scraper is None:
        single_job_scraper = SingleJobScraper()
    # scrap the data
    await single_job_scraper.scrap(data)
