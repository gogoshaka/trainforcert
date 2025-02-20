## Purpose

The `trainforcert.py` script provides several commands to generate and deploy exam-like questions related to Microsoft certifications. The available commands are listed below:

## Environment Setup

### Python Environment
This project has been tested with Python 3.12.0. Please note that earlier versions of Python encountered an issue related to Pydantic support together with OpenAI structured output, as discussed [here](https://community.openai.com/t/issue-with-structured-output-parse-not-working-correctly-beta-object-has-no-attribute-chat-completions-object-has-no-attribute-parse/980137).

To avoid potential conflicts with your existing Python environment, we recommend using [venv](https://docs.python.org/3.12/library/venv.html) and [pyenv](https://github.com/pyenv/pyenv) for isolation.

### Dependencies
Install the required dependencies using the following command:
```console
pip install -r src/requirements.txt
```

### Azure Open AI
This project requires an Azure OpenAI endpoint and key. Please follow the [Azure Open AI quickstart guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line%2Ckeyless%2Ctypescript-keyless%2Cpython-new&pivots=programming-language-python) for setup.

### Secrets
Create a `.env` file in the `src` directory with the following variables:
```
AZURE_OPENAI_ENDPOINT=<your Azure OpenAI endpoint>
AZURE_OPENAI_KEY=<your Azure OpenAI key>
```

## Usage

### Commands



- **Step 1** - Evaluate if a certification is eligible for scraping by TrainForCert.

Choose the [Microsoft certification](https://learn.microsoft.com/en-us/credentials/browse/?credential_types=certification) you want to train for.
Find the associated course and check if this course is eligible for TrainForCert using the command. The file `microsoft_certifications/microsoft_certifications_reference_list.csv` will be updated with the exam code, certification title, course title, and course or exam URL if the command is successful.
Sometimes, the exam code cannot be extracted from scraping. In such cases, the exam code must be populated manually in `microsoft_certifications/microsoft_certifications_reference_list.csv`. Exam codes can be found in this [GitHub repository](https://github.com/JurgenOnAzure/all-the-exams).

[!IMPORTANT]
All subsequent steps require the certification metadata to be present in `microsoft_certifications/microsoft_certifications_reference_list.csv`.

```console
python trainforcert.py test-only --url=<url_of_the_course>
```

For example:
```console
python trainforcert.py test-only --url=https://learn.microsoft.com/en-us/credentials/certifications/exams/az-400/
```

- **Step 2** - Scrape the content of the course associated with the certification.

The result is dumped in a YAML file in `microsoft_certifications/<Certification code>/official_course_material`.

```console
python trainforcert.py scrap-only --certification_code=<Certification code>
```

For example:
```console
python trainforcert.py scrap-only --certification_code=AZ-400
```

- **Step 3** - Clean the course content from scraping artifacts.

Scraping artifacts are textual elements not related to the course content itself (like "duration for this module: 6 minutes"). This step uses Azure OpenAI LLM.
To modify the default model (4o-mini) and prompt, modify the file `src/config.yml`.
Input file is located in `microsoft_certifications/<Certification code>/official_course_material`. Output file is located in `microsoft_certifications/<Certification code>/cleaned_course_material`.

[!NOTE]
To clean AZ-400 course: 195444 input tokens and 106891 output tokens were consumed.

```console
python trainforcert.py clean-only --certification_code=<Certification code>
```

For example:
```console
python trainforcert.py clean-only --certification_code=AZ-400
```

- **Step 4** - Generate questions for the course.

To modify the default model (4o-mini) and prompt, modify the file `src/config.yml`.
Input file is located in `microsoft_certifications/<Certification code>/cleaned_course_material`. Output file is located in `microsoft_certifications/<Certification code>/question_files/questions.json`.

```console
python trainforcert.py generate-questions --certification_code=<Certification code>
```

For example:
```console
python trainforcert.py generate-questions --certification_code=AZ-400
```

- **Step 5** - Serve the questions via a local web server.

The generated questions file from Step 4 is copied to `src/web/public`. After running the command, the website is accessible through `http