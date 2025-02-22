"""Main module"""

import argparse
from argparse import ArgumentError
import csv
import sys
import logging

import argcomplete

from course import Course, ConfigError, PreviousStepsNeededError
from scrapper.CertificationScrapperService import (
    CertificationScrapperService,
)  # Import the Course class
from scrapper.course_structure.AbstractScrappable import ScrapError
from deploy.deploy import DeployError


class CatalogError(Exception):
    """Custom exception for catalog errors"""


def list_available_certifications() -> None:
    """List the content of the CSV file containing the certifications"""
    try:
        with open(
            "../microsoft_certifications/microsoft_certifications_reference_list.csv",
            newline="",
            encoding="utf-8",
        ) as csvfile:
            reader = csv.reader(csvfile)
            _ = next(reader)  # Skip the header
            for row in reader:
                print(", ".join(row[:2]))
    except FileNotFoundError as e:
        raise CatalogError("Catalog file not found") from e


def get_certification_metadata(certification_code: str) -> tuple:
    """Read the CSV file containing the certifications"""
    try:
        with open(
            "../microsoft_certifications/microsoft_certifications_reference_list.csv",
            newline="",
            encoding="utf-8",
        ) as csvfile:
            reader = csv.reader(csvfile)
            _ = next(reader)  # Skip the header
            for row in reader:
                if row[0] == certification_code:
                    return row[1], row[3]
        raise CatalogError(
            f"Certification code {certification_code} not found in catalog"
        )
    except FileNotFoundError as e:
        raise CatalogError("Catalog file not found") from e


def build_parser() -> argparse.ArgumentParser:
    """Build the command line argument parser"""
    parser = argparse.ArgumentParser(
        description="trainforcert script for learning Microsoft certification course content."
    )
    parser.add_argument("-d", "--debug", action="store_true",
                    help="Scrap only the first 2 pages")
    argcomplete.autocomplete(parser)
    subparsers = parser.add_subparsers(dest="command")

    # Add a subparser for the --test-only command
    subparsers.add_parser(
        "test-only",
        help="check if the URL is the root URL for certification course and if it can be scrapped",
    ).add_argument(
        "--url", required=True, help="The URL required for the --test-only command"
    )

    # Add a subparser for the courses
    subparsers.add_parser("courses", help="Show the list of courses supported")

    subparsers.add_parser(
        "scrap-only",
        help=(
            "Scrap the course content from the url found"
            "in microsoft_certifications_reference_list.csv"
        ),
    ).add_argument(
        "certification_code",
        help="The certification code for the course. --courses to list available courses.",
    )

    subparsers.add_parser(
        "clean-only",
        help="Clean the course content to remove all artifacts not related to the course content",
    ).add_argument(
        "certification_code",
        help="The certification code for the course. --courses to list available courses.",
    )

    subparsers.add_parser(
        "generate-questions",
        help="Generate questions with multiple answers from the cleaned course content",
    ).add_argument(
        "certification_code",
        help="The certification code for the course. --courses to list available courses.",
    )

    subparsers.add_parser(
        "run-questions", help="Run a local webserver to test the generated questions"
    ).add_argument(
        "certification_code",
        help="The certification code for the course. --courses to list available courses.",
    )

    subparsers.add_parser(
        "deploy-questions",
        help="Upload the html/css/js files to the Azure Blob Storage configured for"
        " static website hosting",
    ).add_argument(
        "certification_code",
        help="The certification code for the course. --courses to list available courses.",
    )
    return parser


def main():
    """Main function to parse the command line arguments and call the appropriate function"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()

    if args.command == "test-only":
        print(f"Running in test-only mode with URL: {args.url}")
        certification_scrapper_service = CertificationScrapperService(args.url)
        certification_scrapper_service.check_scrappability()

    if args.command == "courses":
        print("Listing available courses:")
        list_available_certifications()

    if args.command == "scrap-only":
        print(
            f"Running in scrap-only mode for certification: {args.certification_code}"
        )
        certification_title, certification_url = get_certification_metadata(
            args.certification_code
        )
        if certification_url is None:
            print(
                f"Certification code {sys.argv[1]} not found. "
                "Run 'python trainforcert.py courses' to list available courses or"
                " 'python trainforcert.py test-only' to evaluate a new certification"
            )
            raise ArgumentError
        course = Course(args.certification_code, certification_title)
        course.scrap(certification_url, args.debug)

    if args.command == "clean-only":
        print(
            f"Running in clean-only mode for certification: {args.certification_code}"
        )
        certification_title, certification_url = get_certification_metadata(
            args.certification_code
        )
        course = Course(args.certification_code, certification_title)
        course.clean()

    if args.command == "generate-questions":
        print(
            f"Running in generate-questions mode for certification: {args.certification_code}"
        )
        certification_title, certification_url = get_certification_metadata(
            args.certification_code
        )
        if certification_title is None:
            print(
                f"Certification code {sys.argv[1]} not found. "
                "Run 'python trainforcert.py courses' to list available courses or "
                "'python trainforcert.py test-only' to evaluate a new certification"
            )
            raise ArgumentError
        course = Course(args.certification_code, certification_title)
        course.generate_questions()

    if args.command == "run-questions":
        print(
            f"Running in run-questions mode for certification: {args.certification_code}"
        )
        certification_title, certification_url = get_certification_metadata(
            args.certification_code
        )
        course = Course(args.certification_code, certification_title)
        course.run_webserver_locally()

    if args.command == "deploy-questions":
        print(
            f"Running in deploy-questions mode for certification: {args.certification_code}"
        )
        certification_title, certification_url = get_certification_metadata(
            args.certification_code
        )
        course = Course(args.certification_code, certification_title)
        course.deploy_questions_on_azure()


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except (
        ArgumentError,
        CatalogError,
        ConfigError,
        PreviousStepsNeededError,
        DeployError,
        ScrapError,
    ) as e:
        logging.error(e)
    except Exception as e:
        logging.exception("An unexpected error occurred", exc_info=e)
    sys.exit(1)
