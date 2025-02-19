import yaml
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from scrapper.course_structure.Certification import Certification

# Define ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


class CertificationScrapperService:
    def __init__(self, url):
        self.root_url = url
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')  # Run in headless mode if you don't need to see the browser
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(url)

    def scrap_course_content(self, outputfile_path):
        certification = Certification(self.driver)
        certification.scrap()
        with open(outputfile_path, 'w') as outfile:
            yaml.dump(certification.to_dict(), outfile, default_flow_style=False)
        self.driver.quit()

    def check_scrappability(self):
        certification = Certification(self.driver)
        try :
            certifcation_code, certification_title = certification.get_certification_metadata(self.root_url)
            print (f"Certification code: {certifcation_code}")
            certification.scrap(check_mode=True)
            # If no exception is raised, the course is scrappable
            # dumps the course info into the csv file
            with open('../../microsoft_certifications/microsoft_certifications_reference_list.csv', 'a') as file:
                # certification_id, certification_title, course_title, course_path
                file.write(f"{certifcation_code},{certification_title},{certification_title}, {self.root_url}\n")
            print(f"{GREEN}The provided certification is scrappable: {self.root_url}{RESET}")
        except:
            # print exception message
            
            print(f"{RED}The provided certification is not scrappable: {self.root_url}{RESET}")