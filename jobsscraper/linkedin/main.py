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


async def scrap_single_job(data: models.LinkedInJob) -> None:
    """
    data provides a url with more details about this linkedin job
    this method scrap this url's webpage, and enhance the given
    data model with the extracted data
    """
    scraper = SingleJobScraper()
    await scraper.scrap(data)
