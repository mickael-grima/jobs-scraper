import abc
from typing import Iterator

import models


class Database(abc.ABC):
    @abc.abstractmethod
    async def save_jobs(self, jobs: Iterator[models.LinkedInJob]):
        pass
