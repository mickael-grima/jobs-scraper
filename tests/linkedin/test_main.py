from unittest.mock import patch, Mock, AsyncMock

import pytest

from jobsscraper.linkedin import scrap_all_jobs, scrap_single_job


@patch("jobsscraper.linkedin.main.AllJobsScraper")
def test_scrap_all_jobs(scraper: Mock):
    list(scrap_all_jobs("Garmisch"))
    scraper.assert_called_once_with("Garmisch", headless=True)
    scraper.return_value.scrap_jobs.assert_called_once_with(keywords="", until=86400)


@patch("jobsscraper.linkedin.main.SingleJobScraper")
@pytest.mark.asyncio
async def test_scrap_single_job(scraper: Mock):
    scraper.return_value.scrap = AsyncMock()

    # call the methods
    data = Mock()
    await scrap_single_job(data)
    await scrap_single_job(data)

    # test the calls
    scraper.assert_called_once_with()
    assert scraper.return_value.scrap.call_count == 2
    scraper.return_value.scrap.assert_awaited_with(data)
