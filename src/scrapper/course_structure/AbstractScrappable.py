from abc import ABC, abstractmethod
from typing import Callable

from urllib.parse import urljoin

from question.question import Questions

class ScrapError(Exception):
    """Custom exception for scrap errors."""

class AbstractScrappable(ABC):
    @abstractmethod
    def __init__(self, driver):
        self.driver = driver

    @abstractmethod
    def scrap(self, check_mode):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def to_markdown(self):
        pass

    @abstractmethod
    def clean(self, func: Callable[[str], str]):
        pass

    def generate_questions(self, func: Callable[[str], str]) -> Questions:
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data):
        pass

    def _goToPage(self, link):
        link_href = link['href']
        base_url = self.driver.current_url
        full_url = urljoin(base_url, link_href)
        self.driver.get(full_url)
