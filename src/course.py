"""Course class to handle course operations.
This class is responsible for scrapping, cleaning, generating questions,
and deploying the course content.
"""

import json
import os

# import re
import socketserver
# import sys

import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI

from deploy.deploy import Deploy
from question.question import CertificationQuestions, Questions
from scrapper.CertificationScrapperService import CertificationScrapperService
from scrapper.course_structure.Certification import Certification
from web.webserver import MyHttpRequestHandler

# Define ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


class ConfigError(Exception):
    """Custom exception for configuration errors."""

class PreviousStepsNeededError(Exception):
    """Custom exception for previous steps needed errors."""

class Course:
    """Class to handle a single course operations."""
    DIRECTORY_OFFICIAL_COURSE = "official_course_material"
    DIRECTORY_CLEANED_COURSE = "cleaned_course_material"
    DIRECTORY_QUESTIONS = "question_files"
    QUESTION_FILENAME = "questions.json"
    WEB_DIRECTORY = "web/public"
    DIRECTORY_SSML_FILES = "ssml_files"
    DIRECTORY_WAV_FILES = "wav_files"

    def __init__(self, certification_code, certification_title, verbose=False):
        load_dotenv()
        self.certification_code = certification_code
        self.certification_title = certification_title
        self.official_course_file_name = f"{self.certification_code}.yml"
        self.verbose = verbose
        self.input_token_count = 0
        self.output_token_count = 0
        self.course_path = (
            f"../microsoft_certifications/{self.certification_code}"
            f"/{Course.DIRECTORY_CLEANED_COURSE}"
        )
        try:
            with open("config.yml", "r", encoding="utf-8") as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError as e:
            raise ConfigError("config.yml file not found") from e

        self.llm_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-08-01-preview",
        )

    @staticmethod
    def check_common_requirements():
        """Check if the common requirements are met."""
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            raise ConfigError(
                "AZURE_OPENAI_ENDPOINT not found in the environment variables."
            )
        if not os.getenv("AZURE_OPENAI_KEY"):
            raise ConfigError(
                "AZURE_OPENAI_KEY not found in the environment variables."
            )

    @staticmethod
    def read_file(file_path):
        """Read the content of a file."""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    @staticmethod
    def get_files_content(input_dir):
        """Get the content of all files in a directory."""
        files_content = []
        for filename in os.listdir(input_dir):
            input_file_path = os.path.join(input_dir, filename)
            if os.path.isfile(input_file_path):
                content = Course.read_file(input_file_path)
                files_content.append(content)
        return files_content

    def _get_azure_openai_response(self, llm_model, system_prompt, content):
        """Get response from Azure OpenAI."""
        response = self.llm_client.chat.completions.create(
            model=llm_model,
            max_tokens=16384,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
        )
        self.input_token_count += response.usage.prompt_tokens
        self.output_token_count += response.usage.completion_tokens
        return response.choices[0].message.content.strip()

    def _get_azure_openai_response_structured_output(
        self, llm_model, system_prompt, content, expected_output_format
    ):
        """Get structured output response from Azure OpenAI."""
        response = self.llm_client.beta.chat.completions.parse(
            model=llm_model,
            max_tokens=16384,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            # response_format=list[Question]
            response_format=expected_output_format,
        )
        self.input_token_count += response.usage.prompt_tokens
        self.output_token_count += response.usage.completion_tokens
        return response.choices[0].message.parsed

    def clean(self):
        """Clean the course content using Azure OpenAI."""
        self.input_token_count = 0
        self.output_token_count = 0
        file_name = f"{self.course_path}/{self.official_course_file_name}"
        with open(
            f"{file_name}",
            "r",
            encoding="utf-8",
        ) as file:
            course_content = yaml.safe_load(file)

        if not course_content:
            raise PreviousStepsNeededError(
                f"No file to clean. Make sure the official course material {file_name} exists."
            )

        if "llm_cleaning_model" not in self.config:
            raise ConfigError("llm_cleaning_model not found in config.yml.")
        llm_cleaning_model = self.config["llm_cleaning_model"]

        if "cleaning_prompt" not in self.config:
            raise ConfigError("cleaning_prompt not found in config.yml.")
        cleaning_prompt = self.config["cleaning_prompt"]

        os.makedirs(
            self.course_path,
            exist_ok=True,
        )

        certification = Certification.from_dict(course_content)

        def llm_cleaning_func(text):
            return self._get_azure_openai_response(
                llm_cleaning_model, cleaning_prompt, text
            )

        certification.clean(llm_cleaning_func)

        # Write the cleaned course content to a new YAML file
        with open(
            f"{self.course_path}/{self.official_course_file_name}",
            "w",
            encoding="utf-8",
        ) as file:
            yaml.dump(certification.to_dict(), file, default_flow_style=False)

        print(
            f"Cleaning has consumed {self.input_token_count} input tokens"
            f"and {self.output_token_count} output tokens."
        )
        print(f"{GREEN}Cleaning completed successfully.{RESET}")

    def scrap(self, certification_url, check_mode=False):
        """Scrap the official course content."""
        os.makedirs(
            f"../microsoft_certifications/{self.certification_code}", exist_ok=True
        )
        os.makedirs(
            f"../microsoft_certifications/{self.certification_code}"
            f"/{Course.DIRECTORY_OFFICIAL_COURSE}",
            exist_ok=True,
        )
        os.makedirs(
            f"../microsoft_certifications/{self.certification_code}"
            f"/{Course.DIRECTORY_CLEANED_COURSE}",
            exist_ok=True,
        )

        output_file_path = f"{self.course_path}/{self.official_course_file_name}"
        certification_scrapper_service = CertificationScrapperService(certification_url)
        certification_scrapper_service.scrap_course_content(output_file_path, check_mode)

    def generate_questions(self):
        """Generate questions from the cleaned course content."""
        # check if file exists
        if not os.path.exists(
            f"{self.course_path}/{self.official_course_file_name}"
        ):
            print(
                f"File not found: ../microsoft_certifications/{self.certification_code}"
                f"/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}"
            )
            raise PreviousStepsNeededError(
                " Please run the clean command first."
            )

        os.makedirs(
            f"../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}",
            exist_ok=True,
        )

        if "llm_question_model" not in self.config:
            raise ConfigError("llm_question_model not found in config.yml.")
        llm_question_model = self.config["llm_question_model"]

        if "question_prompt" not in self.config:
            raise ConfigError("question_prompt not found in config.yml.")
        question_prompt = self.config["question_prompt"]

        with open(
            f"{self.course_path}/{self.official_course_file_name}",
            "r",
            encoding="utf-8",
        ) as file:
            cleaned_content = yaml.safe_load(file)
        certification = Certification.from_dict(cleaned_content)

        def llm_questionify_func(text):
            return self._get_azure_openai_response_structured_output(
                llm_question_model, question_prompt, text, Questions
            )

        questions = certification.generate_questions(llm_questionify_func)
        print(questions)
        certification_questions = CertificationQuestions(
            certification_title=f"{self.certification_code} - {self.certification_title}",
            questions=questions,
        )
        # write questions to a single json file
        with open(
            f"{self.course_path}/{Course.QUESTION_FILENAME}",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(certification_questions.model_dump(), file, indent=4)

    def run_webserver_locally(self):
        """Run a web server to serve the questions.json file."""
        # check if questions.json exist for the certification
        if not os.path.exists(
            f"{self.course_path}/{Course.QUESTION_FILENAME}"
        ):
            print(
                f"File not found: {self.course_path}/{Course.QUESTION_FILENAME}"
            )
            raise PreviousStepsNeededError(
                " Please run the generate-questions command first."
            )
        # copy questions.json to web/public
        with open(
            f"{self.course_path}/{Course.QUESTION_FILENAME}",
            "r",
            encoding="utf-8",
        ) as file:
            questions = json.load(file)
        with open(
            f"./{Course.WEB_DIRECTORY}/{Course.QUESTION_FILENAME}",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(questions, file, indent=4)
        handler = MyHttpRequestHandler
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print(f"Serving at port {8000}")
            httpd.serve_forever()

    def deploy_questions_on_azure(self):
        """check if directory exists"""
        if not os.path.exists(f"./{Course.WEB_DIRECTORY}"):
            print(f"{RED} web Directory not found: ./{Course.WEB_DIRECTORY}{RESET}")
            raise PreviousStepsNeededError(
                " Please run the generate-questions command first."
            )
        deploy = Deploy()
        deploy.deploy(
            question_dir_path=(f"../microsoft_certifications/{self.certification_code}"
                               f"/{Course.DIRECTORY_CLEANED_COURSE}"),
            question_file_name=Course.QUESTION_FILENAME,
        )

    # pylint: disable=line-too-long
    # def speechify(self):
    #     # check if directory exists
    #     if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}'):
    #         print(f"Directory not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}")
    #         print(' Please run the transcriptify command first.')
    #         sys.exit(1)

    #     if not os.getenv("SPEECH_KEY"):
    #         print("SPEECH_KEY not found in the environment variables.")
    #         sys.exit(1)
    #     if not os.getenv("SPEECH_REGION"):
    #         print("SPEECH_REGION not found in the environment variables.")
    #         sys.exit(1)
    #     if "speech_voice" not in self.config:
    #         print("speech_voice not found in config.yml.")
    #         sys.exit(1)

    #     speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), region=os.getenv('SPEECH_REGION'))
    #     audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    #     speech_config.speech_synthesis_voice_name=self.config["speech_voice"]

    #     speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    #     ssml_string = open("ssml.xml", "r").read()
    #     speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml_string).get()

    #     stream = speechsdk.AudioDataStream(speech_synthesis_result)
    #     stream.save_to_wav_file(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_WAV_FILES}/file.wav')

    #         def transcriptify(self):
    #     # check if file exists
    #     if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}'):
    #         print(f"File not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}")
    #         print(' Please run the clean command first.')
    #         sys.exit(1)

    #     if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}'):
    #         os.makedirs(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}')

    #     if "llm_transcript_model" not in self.config:
    #         print("llm_transcript_model not found in config.yml.")
    #         sys.exit(1)
    #     llm_transcript_model =  self.config["llm_transcript_model"]

    #     if "transcript_prompt" not in self.config:
    #         print("llm_transcript_prompt not found in config.yml.")
    #         sys.exit(1)
    #     transcript_prompt =  self.config["transcript_prompt"]

    #     with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}', 'r') as file:
    #         cleaned_content = yaml.safe_load(file)
    #     certification = Certification.from_dict(cleaned_content)

    #     def llm_transcriptify_func(text):
    #         return self._get_azure_openai_response(llm_transcript_model, transcript_prompt, text)

    #     transcripts = certification.transcriptify(llm_transcriptify_func)
    #     # add index to the loop

    #     for i, transcript in enumerate(transcripts):
    #         # convert transcript title into a valid filename
    #         normalized_title = re.sub(r"\W+", "_", transcript["title"])
    #         transcript_title = f'{i}_{normalized_title}.xml'
    #         with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}/{transcript_title}', 'w') as file:
    #             file.write(transcript['transcript'])
