from typing import List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from question.question import Question
from .AbstractScrappable import AbstractScrappable, ScrapError
from .Unit import Unit


class Module(AbstractScrappable):
    def __init__(
        self, module_title: str, units_in_module: List[Unit] = None, driver=None
    ):
        super().__init__(driver)
        self.module_title = module_title
        self.units_in_module = units_in_module if units_in_module else []

    def scrap(self, check_mode=False):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "unit-list"))
            )
        except WebDriverException as e:
            raise ScrapError(
                "Unable to find element with 'id=unit-list'"
            ) from e

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        units_section = soup.find(id="unit-list")
        links = units_section.find_all("a", href=True)
        for i, link in enumerate(links):
            if check_mode and i == 2:
                break
            unit_title = link.get_text(strip=True)
            print(f"    ### {unit_title}")
            self._goToPage(link)
            unit = Unit(unit_title=unit_title, driver=self.driver)
            unit.scrap(check_mode)
            self.units_in_module.append(unit)
            self.driver.back()

    def clean(self, func: Callable[[str], str]):
        for unit in self.units_in_module:
            unit.clean(func)

    def generate_questions(self, func: Callable[[str], str]) -> List[Question]:
        questions = []
        for unit in self.units_in_module:
            questions.extend(unit.generate_questions(func))
        return questions

    def to_dict(self):
        return {
            "module_title": self.module_title,
            "units_in_module": [unit.to_dict() for unit in self.units_in_module],
        }

    def to_markdown(self):
        return f"## {self.module_title}\n{[unit.to_markdown() for unit in self.units_in_module]}"

    @staticmethod
    def from_dict(data):
        units = [Unit.from_dict(u) for u in data["units_in_module"]]
        return Module(module_title=data["module_title"], units_in_module=units)
