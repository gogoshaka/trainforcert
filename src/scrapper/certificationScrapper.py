import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, TypedDict
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from question.question import Question, Questions


class LearningPathTranscript(TypedDict):
    title: str
    transcript: str
