import sys
from typing import List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from question.question import Question
from .AbstractScrappable import AbstractScrappable
from .Module import Module

class LearningPath(AbstractScrappable):
    # statiic constants
    CSS_SELECTOR = '[data-bi-name="module"]'
    def __init__(self, learning_path_title: str, modules_in_learning_path: List[Module] = None, driver=None):
        super().__init__(driver)
        self.learning_path_title = learning_path_title
        self.modules_in_learning_path = modules_in_learning_path if modules_in_learning_path else []

    def scrap(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR,  LearningPath.CSS_SELECTOR)))
        except:
            print("No elements with '[data-bi-name=module] found.")
            sys.exit(1)
         # wait for 60 seconds
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        #time.sleep(60)
        #divs = soup.find_all('div', class_='module')
        divs = soup.find_all('div', {'data-bi-name': 'module'})
        for div in divs:
            link = div.find('a', href=True, text=True)
            module_title = link.get_text(strip=True)
            print(f"  ## {module_title}")
            self._goToPage(link)
            module = Module(module_title=module_title, driver=self.driver)
            module.scrap()
            self.modules_in_learning_path.append(module)
            self.driver.back()

    def clean(self, func: Callable[[str], str]):
        for module in self.modules_in_learning_path:
            module.clean(func)
    
    def generate_questions(self, func: Callable[[str], str]) -> List[Question]:
        questions = []
        for module in self.modules_in_learning_path:
            questions.extend( module.generate_questions(func))
        return questions

    def to_dict(self):
        return {
            'learning_path_title': self.learning_path_title,
            'modules_in_learning_path': [module.to_dict() for module in self.modules_in_learning_path]
        }
    
    def to_markdown(self):
        return f'# {self.learning_path_title}\n{[module.to_markdown() for module in self.modules_in_learning_path]}'
        
    
    @staticmethod
    def from_dict(data):
        modules = [Module.from_dict(m) for m in data['modules_in_learning_path']]
        return LearningPath(learning_path_title=data['learning_path_title'], modules_in_learning_path=modules)