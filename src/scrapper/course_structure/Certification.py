import re
from typing import List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from question.question import LearningPathQuestions
from .AbstractScrappable import AbstractScrappable, ScrapError
from .LearningPath import LearningPath


class Certification(AbstractScrappable):
    def __init__(self, driver=None):
        super().__init__(driver)
        self.certification_content = []

    def get_certification_metadata(self, root_url) -> tuple[str|None, str]:
        """
        Get the certification code and title from the certification url 
        :param root_url: url of the certification
        :return: certification code and title
        raises ValueError if unable to find certification title in the page"""
        # if url does not start by learn.microsoft.com, it is not a valid certification url
        if not root_url.startswith("https://learn.microsoft.com"):
            print(
                "Invalid Microsoft certification URL,"
                " it has to start by 'https://learn.microsoft.com'"
            )
            raise ScrapError("Invalid Microsoft certification URL")

        # get certification code from the last segment of the url
        match = re.search(r"/([a-z]{2}-\d{3})/?$", root_url)
        if not match:
            print("Invalid Microsoft certification code")
            certification_code = None
        else:
            certification_code = match.group(1)

        try:
            # wait for the whole page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )
            # wait for h1 of class title to be present
            WebDriverWait(self.driver, 10).until(
                lambda driver: EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.title")
                )
            )
            certification_title = self.driver.find_element(
                By.CSS_SELECTOR, "h1.title"
            ).text
        except Exception as e:
            print(f"Unable to find certification title in the page: {e}")
            raise ScrapError("Unable to find certification title in the page") from e
        return certification_code, certification_title

    def scrap(self, check_mode=False):
        """Scrap the certification content"
        param check_mode: if True, scrap only the first 2 learning paths
        raises ScrapError if unable to find elements with id starting with 'learn.wwl'"""
        try:
            # wait for the whole page to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )

            WebDriverWait(self.driver, 10).until(
                lambda driver: len(
                    driver.find_elements(By.CSS_SELECTOR, 'a[id^="learn.wwl"]')
                )
                >= 3
            )
        except WebDriverException as e:
            raise ScrapError(
                "Scrapping failure: unable to find elements with id starting with 'learn.wwl'"
            ) from e
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        learning_paths_section = soup.find(id="learning-paths-list")
        links = learning_paths_section.find_all("a", href=True, class_="card-title")
        for i, link in enumerate(links):
            # check_mode is used to test the first 2 learning paths
            if check_mode and i == 2:
                break
            learning_path_title = link.get_text(strip=True)
            print(f"# {learning_path_title}")
            self._goToPage(link)
            learning_path = LearningPath(
                learning_path_title=learning_path_title, driver=self.driver
            )
            learning_path.scrap(check_mode=check_mode)
            self.certification_content.append(learning_path.to_dict())
            self.driver.back()

    def clean(self, func: Callable[[str], str]):
        for learning_path in self.certification_content:
            learning_path.clean(func)

    # def transcriptify(self, func: Callable[[str], str]) -> List[LearningPathTranscript]:
    #     learning_path_transcript = []
    #     for learning_path in self.certification_content:
    #         learning_path_transcript.append({
    #             'title': learning_path.learning_path_title,
    #             'transcript': func(learning_path.to_markdown())
    #         })
    #     return learning_path_transcript

    def generate_questions(
        self, func: Callable[[str], str]
    ) -> List[LearningPathQuestions]:
        questions = []
        for learning_path in self.certification_content:
            questions.append(
                {
                    "learning_path_title": learning_path.learning_path_title,
                    "questions": learning_path.generate_questions(func),
                }
            )
            print(questions)
        return questions

    def to_dict(self):
        return {
            "certification_content": [
                lp if isinstance(lp, dict) else lp.to_dict()
                for lp in self.certification_content
            ]
        }

    def to_markdown(self):
        return f"{[learning_path.to_markdown() for learning_path in self.certification_content]}"

    @staticmethod
    def from_dict(data):
        certification = Certification()
        certification.certification_content = [
            LearningPath.from_dict(lp) for lp in data["certification_content"]
        ]
        return certification
