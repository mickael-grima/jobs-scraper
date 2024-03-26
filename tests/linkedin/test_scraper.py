import asyncio
import os
from contextlib import asynccontextmanager
from itertools import repeat
from typing import Any
from unittest.mock import Mock, patch, AsyncMock

import aiohttp
import pytest
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By

import jobsscraper.linkedin as lkd

dir_ = os.path.dirname(os.path.abspath(__file__))


with open(f"{dir_}/job.html.test") as f:
    html_data = f.read()


def mock_driver() -> Mock:
    mocked_driver = Mock()

    # how many times the search button was found calling find_element
    mocked_driver.button_count = 0
    # how many times the jobs list was found calling find_element
    mocked_driver.jobs_list_count = 0

    def mock_job() -> Mock:
        job = Mock()

        def find_element(by: By, value: Any) -> Any:
            nonlocal job

            # Fails the first time find_element is called
            # this way we simulate a job that can't be scraped correctly
            if by == By.TAG_NAME and job.find_element.call_count == 1:
                raise ValueError

            # Simulate the fact that logo and benefits, time to time,
            # don't exist
            if (  # fails 1 / 2 times for logo and benefits
                    value in {lkd.scraper.logo_class_name, lkd.scraper.benefits_class_name} and
                    job.find_element.call_count % 2 == 0
            ):
                raise NoSuchElementException("")

            res = Mock()
            res.get_attribute.return_value = "url"
            res.text = "title"
            res.find_element.return_value.get_attribute.return_value = "company_url"
            res.find_element.return_value.text = "company_name"
            return res

        job.find_element = Mock(side_effect=find_element)
        return job

    def find_element(_: By, value: Any) -> Any:
        """
        If the searched element is the "More" button:
        - raise NoSuchElementException on the 1st call
        - raise ElementNotInteractableException on the 2nd call
        - return a working button on the 3rd
        """
        nonlocal mocked_driver
        match value:
            # the search button
            case lkd.scraper.more_button_class_name:
                mocked_driver.button_count += 1
                if mocked_driver.button_count == 7:
                    raise NoSuchElementException("")
                button = Mock()
                if mocked_driver.button_count == 2:
                    button.click = Mock(side_effect=ElementNotInteractableException)
                return button
            # the jobs list element
            case lkd.scraper.jobs_results_class_name:
                mocked_driver.jobs_list_count += 1
                jobs_list = Mock()
                job = mock_job()
                if mocked_driver.jobs_list_count == 1:
                    jobs_list.find_elements = Mock(side_effect=NoSuchElementException)
                # the number of jobs keep on increasing, but not unlimited
                elif mocked_driver.jobs_list_count <= 6:
                    jobs = list(repeat(job, 5 * mocked_driver.jobs_list_count))
                    jobs_list.find_elements = Mock(return_value=jobs)
                else:
                    jobs = list(repeat(job, 30))
                    jobs_list.find_elements = Mock(return_value=jobs)
                return jobs_list

    mocked_driver.find_element = Mock(side_effect=find_element)
    return mocked_driver


@patch('time.sleep', return_value=None)
def test_AllJobsScraper_scrap_jobs(_):
    mocked_driver = mock_driver()

    with patch("selenium.webdriver.Chrome", return_value=mocked_driver):
        scraper = lkd.scraper.AllJobsScraper("Garmisch")
        scraper._scraping_jobs_timeout = 0.6
        jobs = list(scraper.scrap_jobs(keywords="Python", until=86400))

        # all jobs should have been fetched
        # 5 jobs couldn't be scraped (5 iterations)
        assert len(jobs) == 25
        assert mocked_driver.find_element.call_count > 10


@pytest.mark.asyncio
async def test_SingleJobScraper_scrap():
    data = lkd.LinkedInJob(
        url="http://test.com/path",
        title="title",
        company=lkd.Company(name="company"),
        location=lkd.Location(full_location="Garmisch"),
    )

    def session(res_status_code: int = 200):
        sess = Mock()
        sess.nb_req = 0

        @asynccontextmanager
        async def get(*args, **kwargs):
            sess.nb_req += 1
            resp = Mock()
            resp.status = res_status_code
            resp.text = AsyncMock(return_value=html_data)
            if res_status_code >= 400:
                resp.raise_for_status = Mock(side_effect=aiohttp.ClientError)
            yield resp

        sess.get = get
        return sess

    # case when the LinkedIn server responds with a 500
    mocked = session(500)
    with patch("aiohttp.ClientSession", return_value=mocked):
        scraper = lkd.scraper.SingleJobScraper(rqs=5)
        with pytest.raises(aiohttp.ClientError):
            await scraper.scrap(data)
        assert mocked.nb_req == 1

    # case when there are too many requests - 429 error code
    mocked = session(429)
    with patch("aiohttp.ClientSession", return_value=mocked):
        scraper = lkd.scraper.SingleJobScraper(rqs=5)
        with pytest.raises(aiohttp.ClientError):
            await scraper.scrap(data)
        assert mocked.nb_req == 6

    # everything went fine
    mocked = session()
    with patch("aiohttp.ClientSession", return_value=mocked):
        scraper = lkd.scraper.SingleJobScraper(rqs=5)
        await scraper.scrap(data)
        assert len(data.description) > 0
        assert len(data.criteria) > 0
        assert mocked.nb_req == 1

    # concurrent calls
    mocked = session()
    with patch("aiohttp.ClientSession", return_value=mocked):
        data.description = ""
        data.criteria = {}
        scraper = lkd.scraper.SingleJobScraper()
        await asyncio.wait([
            asyncio.ensure_future(scraper.scrap(data)),
            asyncio.ensure_future(scraper.scrap(data))
        ])
        assert len(data.description) > 0
        assert len(data.criteria) > 0
        assert mocked.nb_req == 2
