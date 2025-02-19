import os
import socketserver
import sys
import yaml
import re
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

from scrapper.course_structure.Certification import Certification
from scrapper.CertificationScrapperService import CertificationScrapperService

from deploy.deploy import Deploy
from question.question import Questions, CertificationQuestions
from web.webserver import MyHttpRequestHandler


# Define ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"



class Course:
    DIRECTORY_OFFICIAL_COURSE = "official_course_material"
    DIRECTORY_CLEANED_COURSE = "cleaned_course_material"
    DIRECTORY_QUESTIONS = "question_files"
    QUESTION_FILENAME = "questions.json"
    WEB_DIRECTORY= "web/public"
    DIRECTORY_SSML_FILES = "ssml_files"
    DIRECTORY_WAV_FILES = "wav_files"

    def __init__(self, certification_code, certification_title, verbose=False):
        load_dotenv()
        self.certification_code = certification_code
        self.certification_title = certification_title
        self.official_course_file_name = f"{self.certification_code}.yml"
        self.verbose = verbose  
        try:
            with open("config.yml", "r") as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            print("config.yml file not found.")
            sys.exit(1)

        self.llm_client = AzureOpenAI(
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
            api_key=os.getenv("AZURE_OPENAI_KEY"),  
            api_version="2024-08-01-preview"
        )



    @staticmethod
    def check_common_requirements():
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            print("AZURE_OPENAI_ENDPOINT not found in the environment variables.")
            sys.exit(1)
        if not os.getenv("AZURE_OPENAI_KEY"):
            print("AZURE_OPENAI_KEY not found in the environment variables.")
            sys.exit(1)

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as file:
            return file.read()
        
    @staticmethod    
    def get_files_content(input_dir):
        files_content = []
        for filename in os.listdir(input_dir):
            input_file_path = os.path.join(input_dir, filename)
            if os.path.isfile(input_file_path):
                content = Course.read_file(input_file_path)
                files_content.append(content)
        return files_content
    
    
    def _get_azure_openai_response(self, llm_model, system_prompt, content):
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
                }
            ]
        )
        return response.choices[0].message.content.strip()
    
    def _get_azure_openai_response_structured_output(self, llm_model, system_prompt, content, expected_output_format):
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
                }
            ],
            #response_format=list[Question]
            response_format=expected_output_format
            
        )
        return response.choices[0].message.parsed
    

    def clean(self):
        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_OFFICIAL_COURSE}/{self.official_course_file_name}', 'r') as file:
            course_content = yaml.safe_load(file)
    
        if not course_content:
            print(f"No file to clean. Make sure the official course material on the following path: microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_OFFICIAL_COURSE}/{self.official_course_file_name}")
            sys.exit(1)

        if "llm_cleaning_model" not in self.config:
            print("llm_cleaning_model not found in config.yml.")
            sys.exit(1)
        llm_cleaning_model =  self.config["llm_cleaning_model"]

        if "cleaning_prompt" not in self.config:
            print("cleaning_prompt not found in config.yml.")
            sys.exit(1)
        cleaning_prompt =  self.config["cleaning_prompt"]
        
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}'):
            os.makedirs(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}')

        certification = Certification.from_dict(course_content)

        def llm_cleaning_func(text):
            return self._get_azure_openai_response(llm_cleaning_model, cleaning_prompt, text)
        certification.clean(llm_cleaning_func)

        # Write the cleaned course content to a new YAML file
        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}', 'w') as file:
            yaml.dump(certification.to_dict(), file, default_flow_style=False)

                    
    def scrap(self, certification_url):
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}'):
            os.makedirs(f'../microsoft_certifications/{self.certification_code}')
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_OFFICIAL_COURSE}'):
            os.makedirs(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_OFFICIAL_COURSE}')
        outputfilepath = f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_OFFICIAL_COURSE}/{self.official_course_file_name}'
        certificationScrapperService = CertificationScrapperService(certification_url)
        certificationScrapperService.scrap_course_content(outputfilepath)


            
    def generate_questions(self):
        # check if file exists
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}'):
            print(f"File not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}")
            print(' Please run the clean command first.')
            sys.exit(1)

        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}'):
            os.makedirs(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}')
        
        if "llm_question_model" not in self.config:
            print("llm_question_model not found in config.yml.")
            sys.exit(1)
        llm_question_model =  self.config["llm_question_model"]

        if "question_prompt" not in self.config:
            print("question_prompt not found in config.yml.")
            sys.exit(1)
        question_prompt =  self.config["question_prompt"]

        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}', 'r') as file:
            cleaned_content = yaml.safe_load(file)
        certification = Certification.from_dict(cleaned_content)

        def llm_questionify_func(text):
            return self._get_azure_openai_response_structured_output(llm_question_model, question_prompt, text, Questions)
        
        questions = certification.generate_questions(llm_questionify_func)
        print(questions)
        certificationQuestions = CertificationQuestions(certification_title=f'{self.certification_code} - {self.certification_title}', questions=questions)
        # write questions to a single json file
        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}/{Course.QUESTION_FILENAME}', 'w') as file:
            json.dump(certificationQuestions.model_dump(), file, indent=4)

    def run_webserver_locally(self):
        # check if questions.json exist for the certification
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}/{Course.QUESTION_FILENAME}'):
            print(f"File not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}/{Course.QUESTION_FILENAME}")
            print(' Please run the generate_questions command first.')
            sys.exit(1)
        # copy questions.json to web/public
        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}/{Course.QUESTION_FILENAME}', 'r') as file:
            questions = json.load(file)
        with open(f'./{Course.WEB_DIRECTORY}/{Course.QUESTION_FILENAME}', 'w') as file:
            json.dump(questions, file, indent=4)
        handler = MyHttpRequestHandler
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print(f"Serving at port {8000}")
            httpd.serve_forever()
    
    def deploy_questions_on_azure(self):
        # check if directory exists
        if not os.path.exists(f'./{Course.WEB_DIRECTORY}'):
            print(f"{RED} web Directory not found: ./{Course.WEB_DIRECTORY}{RESET}")
            print(' Please run the generate_questions command first.')
            sys.exit(1)
        deploy = Deploy()
        deploy.deploy(question_dir_path=f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_QUESTIONS}', question_file_name=Course.QUESTION_FILENAME)

    '''
    def speechify(self):
        # check if directory exists
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}'):
            print(f"Directory not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}")
            print(' Please run the transcriptify command first.')
            sys.exit(1)

        if not os.getenv("SPEECH_KEY"):
            print("SPEECH_KEY not found in the environment variables.")
            sys.exit(1)
        if not os.getenv("SPEECH_REGION"):
            print("SPEECH_REGION not found in the environment variables.")
            sys.exit(1)
        if "speech_voice" not in self.config:
            print("speech_voice not found in config.yml.")
            sys.exit(1)

        speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), region=os.getenv('SPEECH_REGION'))
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        speech_config.speech_synthesis_voice_name=self.config["speech_voice"]

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)


        ssml_string = open("ssml.xml", "r").read()
        speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml_string).get()

        stream = speechsdk.AudioDataStream(speech_synthesis_result)
        stream.save_to_wav_file(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_WAV_FILES}/file.wav')


            def transcriptify(self):
        # check if file exists
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}'):
            print(f"File not found: ../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}")
            print(' Please run the clean command first.')
            sys.exit(1)
        
        if not os.path.exists(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}'):
            os.makedirs(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}')

        if "llm_transcript_model" not in self.config:
            print("llm_transcript_model not found in config.yml.")
            sys.exit(1)
        llm_transcript_model =  self.config["llm_transcript_model"]

        if "transcript_prompt" not in self.config:
            print("llm_transcript_prompt not found in config.yml.")
            sys.exit(1)
        transcript_prompt =  self.config["transcript_prompt"]

        with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_CLEANED_COURSE}/{self.official_course_file_name}', 'r') as file:
            cleaned_content = yaml.safe_load(file)
        certification = Certification.from_dict(cleaned_content)

        def llm_transcriptify_func(text):
            return self._get_azure_openai_response(llm_transcript_model, transcript_prompt, text)
        
        transcripts = certification.transcriptify(llm_transcriptify_func)
        # add index to the loop

        for i, transcript in enumerate(transcripts):
            # convert transcript title into a valid filename
            normalized_title = re.sub(r"\W+", "_", transcript["title"])
            transcript_title = f'{i}_{normalized_title}.xml'
            with open(f'../microsoft_certifications/{self.certification_code}/{Course.DIRECTORY_SSML_FILES}/{transcript_title}', 'w') as file:
                file.write(transcript['transcript'])
    '''

        