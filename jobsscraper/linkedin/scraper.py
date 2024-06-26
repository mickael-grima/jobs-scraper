import asyncio
import logging
import time
from asyncio import Semaphore
from typing import Iterator
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.webdriver import WebDriver, Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from . import models, utils

__all__ = ["AllJobsScraper", "SingleJobScraper"]

linkedin_search_url = "https://www.linkedin.com/jobs/search"

more_button_class_name = "infinite-scroller__show-more-button"
jobs_results_class_name = "jobs-search__results-list"
logo_class_name = "search-entity-media"
benefits_class_name = "result-benefits__text"


class AllJobsScraper:
    # how long we try to scrap new jobs after
    # scrolling down or clicking on More Jobs button
    _scraping_jobs_timeout = 6

    def __init__(self, location: str, *, headless: bool = True):
        # location can be a country, state or city
        # ex: Germany | Munich | Munich, Bavaria, Germany
        self._location = location

        # The index of the job that has been last scraped
        # Since LinkedIn has an infinite scrolling, this is important
        # to remember where we are with the scraping
        self._job_index: int = 0

        self._driver = self.__create_driver(headless=headless)

    @staticmethod
    def __create_driver(headless: bool = True) -> WebDriver:
        """
        Create the WebDriver used to execute command on the Chrome browser
        :param headless: if true, start a headless browser. Otherwise, it is headfull
        """
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        return webdriver.Chrome(options=options)

    @utils.take_screenshot_on_error
    def scrap_jobs(self, keywords: str = "", *, until: int = -1) -> Iterator[models.LinkedInJob]:
        """
        Go through the LinkedIn search page and scrap all the jobs there
        Not everything is shown, one need to scroll down or click on "Load More"
        to load more jobs

        :param keywords: search using those keywords. If empty, search for all jobs
        :param until: How long in the past we should scrap jobs. -1 means no limit
        :return: An iterator of LinkedIn Jobs
        """
        logging.info(f"Start scrapping jobs from LinkedIn: location={self._location}")

        # build URL
        params = {"location": self._location}
        if until >= 0:
            params["f_TPR"] = until
        if keywords != "":
            params["keywords"] = keywords
        url = f"{linkedin_search_url}?{urlencode(params)}"

        # navigate to the page
        self._driver.get(url)

        # Start scraping
        jobs = self.__scrap_new_jobs()
        nb_tries = 0
        counter = 0
        while nb_tries < 10:
            for job in jobs:
                yield job
                counter += 1
                nb_tries = 0  # reset it since we were able to fetch jobs
            # scroll down/click button to load more jobs
            if not self.__load_more_jobs():
                break
            jobs = self.__scrap_new_jobs()
            if len(jobs) == 0:
                logging.debug("No jobs found. Retrying ...")
                nb_tries += 1
                time.sleep(1)
                continue
            logging.info(f"Scrapped {counter} jobs until now ...")

        logging.info(f"Finished scrapping jobs from LinkedIn: country={self._location}")

    def __load_more_jobs(self) -> bool:
        """
        LinkedIn has 2 solutions to load more jobs:
        - a button at the end of the page. But it is not always clickable, and if this is the case
          we simply scroll down
        - by scrolling down
        """
        try:
            button = self._driver.find_element(By.CLASS_NAME, more_button_class_name)
            button.click()
            return True
        except NoSuchElementException:
            return False
        except ElementNotInteractableException:  # button can't be clicked
            # scroll up and then down to load more jobs
            # sometimes scrolling down doesn't work immediately,
            # and scrolling up and then down again fixes the problem
            self._driver.execute_script("window.scrollTo(0, 0);")
            self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            return True

    def __scrap_new_jobs(self) -> list[models.LinkedInJob]:
        """
        At this step, we have already loaded more job (by either clicking or scrolling down)
        and we need to fetch the new jobs. We might need to wait until it the content is fully
        loaded

        :param driver: Chrome driver

        :return: the list of new found jobs
        """
        # Find all list elements. Since we just scrolled down, retry several times
        jobs: list[WebElement] = []
        start = time.time()
        while time.time() - start < self._scraping_jobs_timeout and len(jobs) == 0:
            try:
                jobs_list = self._driver.find_element(By.CLASS_NAME, jobs_results_class_name)
                jobs = jobs_list.find_elements(By.TAG_NAME, "li")[self._job_index:]
            except NoSuchElementException:
                pass  # continue: it might load later
            time.sleep(0.2)  # sleep a bit

        self._job_index += len(jobs)

        # format found jobs
        res: list[models.LinkedInJob] = []
        for job in jobs:
            linkedin_job = self.__scrap_single_job(job)
            if linkedin_job is None:
                continue
            res.append(linkedin_job)
        return res

    @utils.silent_log_error()
    def __scrap_single_job(self, job: WebElement) -> models.LinkedInJob:
        return models.LinkedInJob(
            url=self.__get_job_link(job),
            title=self.__get_job_title(job),
            company=self.__get_job_company(job),
            location=self.__get_job_location(job),
            posted_time=self.__get_job_posted_time(job),
        )

    @staticmethod
    def __get_job_link(job: WebElement) -> str:
        return job.find_element(By.TAG_NAME, "a").get_attribute("href")

    @staticmethod
    def __get_job_title(job: WebElement) -> str:
        return job.find_element(By.TAG_NAME, "h3").text.strip()

    @staticmethod
    def __get_job_company(job: WebElement) -> models.Company:
        link = job.find_element(By.TAG_NAME, "h4").find_element(By.TAG_NAME, "a")
        try:
            logo = job.find_element(
                By.CLASS_NAME, logo_class_name).find_element(
                By.TAG_NAME, "a").get_attribute("data-ghost-url")
        except (AttributeError, NoSuchElementException):
            logo = None
        try:
            benefit = job.find_element(By.CLASS_NAME, benefits_class_name)
        except NoSuchElementException:
            benefit = None
        active_hiring = benefit.text.strip(' "').lower() == "actively hiring" if benefit else None
        return models.Company(
            name=link.text.strip(),
            url=link.get_attribute("href"),
            logo=logo,
            actively_hiring=active_hiring
        )

    @staticmethod
    def __get_job_location(job: WebElement) -> models.Location:
        loc = job.find_element(By.CLASS_NAME, "job-search-card__location").text.strip()
        return models.Location(full_location=loc)

    @staticmethod
    @utils.silent_log_error(log_level=logging.DEBUG)
    def __get_job_posted_time(job: WebElement) -> str:
        return job.find_element(
            By.CLASS_NAME, "job-search-card__listdate--new").get_attribute("datetime")


class SingleJobScraper:
    """
    Scrap LinkedIn single job pages
    Control the number of request per second to the linkedin servers
    Also, has a retry mechanism in case 429 error codes are caught
    """

    def __init__(self, *, nb_retries: int = 5, rqs: int = 1):
        """
        :param nb_retries: How many times we retry an http call in case of a 429 error code
        :param rqs: number of requests allowed per second
        """
        self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(
            ssl=False,
        ))

        self._nb_retries = nb_retries
        self._sem = Semaphore(rqs)

    def __del__(self):
        self._session._connector._close()

    async def __request(self, url: str, *, retry_no: int = 0) -> str:
        """
        Get the html page by requesting the URL
        Retry if 429 status code
        """
        # acquire the right to make a call depending on how many per second we can do
        await self.__acquire_call()
        status: int = -1
        try:
            async with self._session.get(url) as resp:
                status = resp.status
                print(status)
                resp.raise_for_status()
                return await resp.text()
        except aiohttp.ClientError:
            if status == 429:
                if retry_no >= self._nb_retries:
                    logging.exception(f"Too many requests, even after {retry_no} retries")
                    raise
                return await self.__request(url, retry_no=retry_no + 1)
            logging.exception(f"Failed with status={status}")
            raise

    async def __acquire_call(self):
        """
        acquire a call during 1sec
        releasing the semaphore is done in background
        independently on the status of any other tasks
        """
        await self._sem.acquire()

        async def release():
            await asyncio.sleep(1)
            self._sem.release()

        asyncio.ensure_future(asyncio.shield(release()))

    async def scrap(self, data: models.LinkedInJob):
        html = await self.__request(data.url)
        soup = BeautifulSoup(html, "lxml")
        self.__scrap_description(data, soup)
        self.__scrap_criteria(data, soup)

    @staticmethod
    @utils.silent_log_error()
    def __scrap_description(data: models.LinkedInJob, soup: BeautifulSoup):
        data.description = soup.find_all("div", attrs={"class": "show-more-less-html__markup"})[0].text

    @utils.silent_log_error()
    def __scrap_criteria(self, data: models.LinkedInJob, soup: BeautifulSoup):
        for li in soup.find_all("li", attrs={"class": "description__job-criteria-item"}):
            criterium, value = get_criterium(li)
            if criterium is not None and value is not None:
                data.criteria[criterium] = value


@utils.silent_log_error(default=(None, None))
def get_criterium(li: Tag) -> (str | None, str | None):
    criterium: str | None = None
    value: str | None = None
    for element in li:
        if element.name == "h3":
            criterium = element.text.strip(" \n")
        if element.name == "span":
            value = element.text.strip(" \n")
    return criterium, value
