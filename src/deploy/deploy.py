"""Deploy a static website to Azure Storage Account."""

import os
import yaml
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient, ContentSettings, StaticWebsite

# Define ANSI escape codes for colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


class DeployError(Exception):
    """Custom exception for deployment errors."""


class Deploy:
    """Deploy a static website to Azure Storage Account."""

    def __init__(self):
        # Determine the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "deploy.yml")
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError as e:
            raise DeployError("deploy.yml file not found.") from e
        if not self.config.get("subscription_id"):
            # print(f"{RED}subscription_id not found in configuration file{RESET}")
            raise DeployError("subscription_id not found in configuration file.")
        self.subscription_id = self.config.get("subscription_id")
        if not self.config.get("resource_group_name"):
            # print(f"{RED}resource_group_name not found in configuration file{RESET}")
            raise DeployError("resource_group_name not found in configuration file.")
        self.resource_group_name = self.config.get("resource_group_name")
        if not self.config.get("storage_account_name"):
            # print(f"{RED}storage_account_name not found in configuration file{RESET}")
            raise DeployError("storage_account_name not found in configuration file.")
        self.storage_account_name = self.config.get("storage_account_name")
        if not self.config.get("location"):
            # print(f"{RED}location not found in configuration file{RESET}")
            raise DeployError("location not found in configuration file.")
        self.location = self.config.get("location")

    def deploy(self, question_dir_path, question_file_name):
        # Authenticate with Azure
        print(f"Authenticating with Azure...{RESET}")
        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False
        )
        storage_client = StorageManagementClient(credential, self.subscription_id)

        # Check if the storage account already exists
        try:
            storage_account = storage_client.storage_accounts.get_properties(
                self.resource_group_name, self.storage_account_name
            )
            print(f"Storage account {self.storage_account_name} does exists.{RESET}")
            properties = storage_client.blob_services.get_service_properties(
                self.resource_group_name, self.storage_account_name
            )
            # TODO: check if the account has Storage blob data contrubutor role assigned

        except ResourceNotFoundError:
            print(
                f"Storage account {self.storage_account_name} does not exist. Creating it now..."
            )
            # Create the storage account
            storage_async_operation = storage_client.storage_accounts.begin_create(
                self.resource_group_name,
                self.storage_account_name,
                {
                    "location": self.location,
                    "sku": {"name": "Standard_LRS"},
                    "kind": "StorageV2",
                    "properties": {"isHnsEnabled": False},
                },
            )
        except HttpResponseError as e:
            raise DeployError(
                f"Error occurred while checking storage account properties: {e.message}"
            ) from e

            # TODO: add the blob data contributor role to the storage account
            # Wait for the operation to complete
            storage_account = storage_async_operation.result()
            print(
                f"Storage account {self.storage_account_name} created successfully.{RESET}"
            )

        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.storage_account_name}.blob.core.windows.net",
            credential=credential,
        )
        properties = storage_client.blob_services.get_service_properties(
            self.resource_group_name, self.storage_account_name
        )
        static_website = StaticWebsite(
            enabled=True,
            index_document="index.html",
            error_document404_path="error.html",
        )
        blob_service_client.set_service_properties(static_website=static_website)

        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.storage_account_name}.blob.core.windows.net",
            credential=credential,
        )

        # check if the container already exists
        try:
            container_client = blob_service_client.get_container_client("$web")
            container_client.get_container_properties()
            print("Container $web already exists.")
        except ResourceNotFoundError:
            print("Container $web does not exist. Creating it now...")
            container_client.create_container()
            print("Container $web created successfully.")
        except HttpResponseError as e:
            raise DeployError(
                f"Error occurred while checking container properties: {e.message}"
            ) from e
        # Upload static files to the container
        local_path = "./web"
        for root, _, files in os.walk(local_path):
            for file in files:
                file_path = os.path.join(root, file)
                blob_client = container_client.get_blob_client(file)
                with open(file_path, "rb") as data:
                    blob_client.upload_blob(
                        data,
                        overwrite=True,
                        content_settings=ContentSettings(content_type="text/html"),
                    )
        print(question_dir_path)
        print(question_file_name)

        # TODO: harmonize the file paths among the different scripts
        question_file_path = question_dir_path + "/" + question_file_name
        # question_file_path = os.path.join(paths=question_dir_path.split('/'), question_file_name)
        blob_client = container_client.get_blob_client(question_file_name)
        with open(question_file_path, "rb") as data:
            print(f"Uploading {question_file_path} to the container...")
            blob_client.upload_blob(
                data=data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json"),
            )

        # Get the primary endpoint for the static website
        primary_endpoint = storage_account.primary_endpoints.web
        print(f"{GREEN}Static website is available at: {primary_endpoint}{RESET}")
