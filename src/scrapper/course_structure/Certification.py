import sys
import re
from typing import List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from question.question import LearningPathQuestions
from .AbstractScrappable import AbstractScrappable
from .LearningPath import LearningPath

class Certification(AbstractScrappable):
    def __init__(self, driver=None):
        super().__init__(driver)
        self.certification_content = []

    def get_certification_metadata(self, root_url):
        # if url does not start by learn.microsoft.com, it is not a valid certification url
        if not root_url.startswith('https://learn.microsoft.com'):
            print ("Invalid Microsoft certification URL, it has to start by 'https://learn.microsoft.com'")
            return None, None

        # get certification code from the last segment of the url
        match = re.search(r'/([a-z]{2}-\d{3})/?$', root_url)
        if not match:
            print("Invalid Microsoft certification code. The provided URL has to end with the certification code like az-900")
            raise ValueError("Unable to parse certficiation code from the provided url")
        certification_code = match.group(1)

        try:
            # wait for h1 of class title to be present
            WebDriverWait(self.driver, 10).until(
                lambda driver: EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.title'))
            )
            certification_title = self.driver.find_element(By.CSS_SELECTOR, 'h1.title').text
        except:
            print("Unable to find certification title in the page")
            raise ValueError("Unable to find certification title in the page")
        return certification_code, certification_title

    def scrap(self, check_mode=False):
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'a[id^="learn.wwl"]')) >= 3)
        except:
            print("Scrapping failure: unable to find elements with id starting with 'learn.wwl'")
            sys.exit(1)
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        learning_paths_section = soup.find(id="learning-paths-list")
        links = learning_paths_section.find_all('a', href=True, class_='card-title')
        for i, link in enumerate(links):
            learning_path_title = link.get_text(strip=True)
            print(f"# {learning_path_title}")
            self._goToPage(link)
            learning_path = LearningPath(learning_path_title=learning_path_title, driver=self.driver)
            learning_path.scrap()
            self.certification_content.append(learning_path.to_dict())
            self.driver.back()
            # check_mode is used to test the first 2 learning paths
            if (check_mode and i == 1):
                break
    
    def clean(self, func: Callable[[str], str]):
        for learning_path in self.certification_content:
            learning_path.clean(func)
    """
    def transcriptify(self, func: Callable[[str], str]) -> List[LearningPathTranscript]:
        learning_path_transcript = []
        for learning_path in self.certification_content:
            learning_path_transcript.append({
                'title': learning_path.learning_path_title,
                'transcript': func(learning_path.to_markdown())
            })
        return learning_path_transcript
    """
    def generate_questions(self, func: Callable[[str], str]) -> List[LearningPathQuestions]:
        questions = []
        for learning_path in self.certification_content:
            questions.append({
                'learning_path_title': learning_path.learning_path_title,
                'questions': learning_path.generate_questions(func)
            })
            print(questions)
        return questions
            

    def to_dict(self):
        return {
            'certification_content': self.certification_content
        }
    
    def to_markdown(self):
        return f'{[learning_path.to_markdown() for learning_path in self.certification_content]}'
    
    @staticmethod
    def from_dict(data):
        certification = Certification()
        certification.certification_content = [LearningPath.from_dict(lp) for lp in data['certification_content']]
        return certification