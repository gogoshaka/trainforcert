from typing import List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from question.question import Question
from .AbstractScrappable import AbstractScrappable, ScrapError


class Unit(AbstractScrappable):
    def __init__(self, unit_title: str, unit_content: str = None, driver=None):
        super().__init__(driver)
        self.unit_title = unit_title
        self.unit_content = unit_content

    def scrap(self, _):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "unit-inner-section"))
            )
        except WebDriverException as e:
            raise ScrapError(
                "Unable to find element with 'id=unit-inner-section'"
            ) from e
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        unit_inner_section = soup.find(id="unit-inner-section")
        self.unit_content = unit_inner_section.get_text(strip=True)

    def clean(self, func: Callable[[str], str]):
        print(f"Cleaning unit: {self.unit_title}")
        self.unit_content = func(self.unit_content)

    def generate_questions(self, func: Callable[[str], str]) -> List[Question]:
        return func(self.unit_content).questions

    def to_dict(self):
        return {"unit_title": self.unit_title, "unit_content": self.unit_content}

    def to_markdown(self):
        return f"### {self.unit_title}\n{self.unit_content}"

    @staticmethod
    def from_dict(data):
        return Unit(unit_title=data["unit_title"], unit_content=data["unit_content"])
