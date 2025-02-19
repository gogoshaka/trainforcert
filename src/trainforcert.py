import csv
import sys
import argparse
import argcomplete

from course import Course
from scrapper.CertificationScrapperService import CertificationScrapperService  # Import the Course class



def list_available_certifications():
# List the content of the CSV file containing the certifications
    with open('../microsoft_certifications/microsoft_certifications_reference_list.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip the header
        for row in reader:
            print(', '.join(row[:2])) 

def get_certification_metadata(certification_code):
    # Read the CSV file containing the certifications
    with open('../microsoft_certifications/microsoft_certifications_reference_list.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip the header
        for row in reader:
            if row[0] == certification_code:
                return row[1], row[3]
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="trainforcert script for learning Microsoft certification course content.")
    argcomplete.autocomplete(parser)
    subparsers = parser.add_subparsers(dest="command")

    # Add a subparser for the --test-only command
    test_only_parser = subparsers.add_parser("test-only",  help="check if the URL is the root URL for certification course and if it can be scrapped")
    test_only_parser.add_argument("--url", required=True, help="The URL required for the --test-only command")

    # Add a subparser for the --test-only command
    list_courses_parser = subparsers.add_parser("courses", help="Show the list of courses supported")

    scrap_parser = subparsers.add_parser("scrap-only", help="Scrap the course content from the url found in microsoft_certifications_reference_list.csv")
    scrap_parser.add_argument("certification_code", help="The certification code for the course. --courses to list available courses.")

    clean_parser = subparsers.add_parser("clean-only", help="Clean the course content to remove all artifacts not related to the course content")
    clean_parser.add_argument("certification_code", help="The certification code for the course. --courses to list available courses.")

    generate_questions_parser = subparsers.add_parser("generate-questions", help="Generate questions with multiple answers from the cleaned course content")
    generate_questions_parser.add_argument("certification_code", help="The certification code for the course. --courses to list available courses.")

    run_questions_parser = subparsers.add_parser("run-questions", help="Run a local webserver to test the generated questions")
    run_questions_parser.add_argument("certification_code", help="The certification code for the course. --courses to list available courses.")

    deploy_questions_parser = subparsers.add_parser("deploy-questions", help="Upload the html/css/js files to the Azure Blob Storage configured for static website hosting")
    deploy_questions_parser.add_argument("certification_code", help="The certification code for the course. --courses to list available courses.")


    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "test-only":
        print(f"Running in test-only mode with URL: {args.url}")
        certificationScrapperService = CertificationScrapperService(args.url)
        certificationScrapperService.check_scrappability()
        sys.exit(0)
    
    if args.command == "courses":
        print(f"Running in test-only mode with URL: {args.url}")
        list_available_certifications()
        sys.exit(0)  
    
    if args.command == "scrap-only":
        print(f"Running in scrap-only mode for certification: {args.certification_code}")
        certification_title, certification_url = get_certification_metadata(args.certification_code)
        if certification_url is None:
            print(f"Certification code {sys.argv[1]} not found. Run 'python trainforcert.py courses' to list available courses or 'python trainforcert.py test-only' to evaluate a new certification")
            sys.exit(1)
        course = Course(args.certification_code, certification_title)

        course.scrap(certification_url)
        sys.exit(0)

    if args.command == "clean-only":
        print(f"Running in clean-only mode for certification: {args.certification_code}")
        certification_title, certification_url = get_certification_metadata(args.certification_code)
        if certification_title is None:
            print(f"Certification code {sys.argv[1]} not found. Run 'python trainforcert.py courses' to list available courses or 'python trainforcert.py test-only' to evaluate a new certification")
            sys.exit(1)
        course = Course(args.certification_code, certification_title)
        course.clean()
        sys.exit(0)

    if args.command == "generate-questions":
        print(f"Running in generate-questions mode for certification: {args.certification_code}")
        certification_title, certification_url = get_certification_metadata(args.certification_code)
        if certification_title is None:
            print(f"Certification code {sys.argv[1]} not found. Run 'python trainforcert.py courses' to list available courses or 'python trainforcert.py test-only' to evaluate a new certification")
            sys.exit(1)
        course = Course(args.certification_code, certification_title)
        course.generate_questions()
        sys.exit(0)

    if args.command == "run-questions":
        print(f"Running in run-questions mode for certification: {args.certification_code}")
        certification_title, certification_url = get_certification_metadata(args.certification_code)
        if certification_title is None:
            print(f"Certification code {sys.argv[1]} not found. Run 'python trainforcert.py courses' to list available courses or 'python trainforcert.py test-only' to evaluate a new certification")
            sys.exit(1)
        course = Course(args.certification_code, certification_title)
        course.run_webserver_locally()
        sys.exit(0)

    if args.command == "deploy-questions":
        print(f"Running in deploy-questions mode for certification: {args.certification_code}")
        certification_title, certification_url = get_certification_metadata(args.certification_code)
        if certification_title is None:
            print(f"Certification code {sys.argv[1]} not found. Run 'python trainforcert.py courses' to list available courses or 'python trainforcert.py test-only' to evaluate a new certification")
            sys.exit(1)
        course = Course(args.certification_code, certification_title)
        course.deploy_questions_on_azure()
        sys.exit(0)

    
