from typing import List, Callable, Dict, Any, TypedDict
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
from urllib.parse import urljoin
from abc import ABC, abstractmethod
import time

from question.question import Question, Questions








    
class LearningPathTranscript(TypedDict):
    title: str
    transcript: str





