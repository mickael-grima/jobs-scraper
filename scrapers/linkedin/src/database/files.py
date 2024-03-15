import os
from typing import Iterator

from .interface import Database
import models


class FileClient(Database):
    """Store the data as files"""
    _jobs_filename_prefix = "jobs"
    _number_jobs_per_file = 10000

    def __init__(self, directory: str):
        """
        :param directory: directory where data will be saved. It has to be an absolute path
        """
        self._directory = directory
        self.__ensure_directory()

    def __ensure_directory(self):
        """Make sure the directory is created"""
        try:
            os.makedirs(self._directory)
        except FileExistsError:
            # directory already exists
            pass

    def __jobs_filename(self, i: int) -> str:
        return os.path.join(
            self._directory,
            f"{self._jobs_filename_prefix}_{i % self._number_jobs_per_file}.jsonl"
        )

    async def save_jobs(self, jobs: Iterator[models.LinkedInJob]):
        """
        This method iterate over all jobs and save them in files
        Each line in a file is a single job as a json object
        Each file contains max 10k jobs

        :param jobs: iterate jobs
        """
        i = 0  # jobs counter

        has_jobs = True
        while has_jobs:
            # collect 10k lines to write into the file
            lines = []
            while len(lines) < self._number_jobs_per_file:
                try:
                    lines.append(next(jobs).json(exclude_none=True))
                except StopIteration:
                    has_jobs = False  # no more jobs left. Stop after this loop is over
                    break

            # write the collected lines in the file
            with open(self.__jobs_filename(i), "w") as f:
                f.write("\n".join(lines))

            i += 1  # counter to create a new file in the next loop