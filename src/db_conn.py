import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pymongo import MongoClient
from cust_logger import logger

# MongoDB configuration
load_dotenv()
from cust_logger import logger
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "apps_db"
COLLECTION_NAME = "applications"

class AbstractDatabaseConn(ABC):
    # absract database connection
    @abstractmethod
    def create_application(self, application_id: str, data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_application(self, application_id: str) -> bool:
        pass

    @abstractmethod
    def log_application_interaction(self, application_id: str, log_entry: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def get_application_logs(self, application_id: str) -> Optional[List[Dict[str, Any]]]:
        pass

class InMemoryDatabaseConn(AbstractDatabaseConn):
    def __init__(self):
        # Initial in-memory storage for applications
        self.applications: Dict[str, Dict] = {}

    def create_application(self, application_id: str, data: Dict[str, Any]) -> str:
        """Creates a new application entry in the in-memory storage and returns the application ID."""
        self.applications[application_id] = data
        return application_id

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an application by ID, if it exists."""
        return self.applications.get(application_id)

    def delete_application(self, application_id: str) -> bool:
        """Deletes an application by ID. Returns True if successful, False if not found."""
        if application_id in self.applications:
            del self.applications[application_id]
            return True
        return False

    def log_application_interaction(self, application_id: str, log_entry: Dict[str, Any]) -> bool:
        """Logs an interaction to an application's log if the application exists."""
        app = self.applications.get(application_id)
        if app:
            app["app_logs"].append(log_entry)
            return True
        return False

    def get_application_logs(self, application_id: str) -> Optional[List[Dict[str, Any]]]:
        """Returns the logs for an application if it exists."""
        app = self.applications.get(application_id)
        return app["app_logs"] if app else None

class MongoDatabaseConn(AbstractDatabaseConn):
    def __init__(self):
        # Initialize MongoDB client and set up the collection
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]

        # Ensure `uuid` is unique by creating a unique index
        self.collection.create_index("uuid", unique=True)

    def create_application(self, application_id: str, data: Dict[str, Any]) -> str:
        """Creates a new application entry in MongoDB using `uuid` as the unique identifier."""
        data["uuid"] = application_id  # Use application_id for uuid field as unique identifier

        self.collection.insert_one(data)
        return application_id

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an application by its `uuid` from MongoDB, if it exists."""
        app = self.collection.find_one({"uuid": application_id})
        return app

    def delete_application(self, application_id: str) -> bool:
        """Deletes an application by its `uuid` from MongoDB. Returns True if successful."""
        result = self.collection.delete_one({"uuid": application_id})
        return result.deleted_count > 0 # if deleted at least 1 (expected only 1 bc of UUID index)

    def log_application_interaction(self, application_id: str, log_entry: Dict[str, Any]) -> bool:
        """Logs an interaction to an application's log in MongoDB, using `uuid` as identifier."""
        result = self.collection.update_one(
            {"uuid": application_id},
            {"$push": {"app_logs": log_entry}}
        )
        return result.modified_count > 0 # if deleted at least 1 (expected only 1 bc of UUID index)

    def get_application_logs(self, application_id: str) -> Optional[List[Dict[str, Any]]]:
        """Returns the logs for an application in MongoDB, using `uuid` as the identifier."""
        app = self.collection.find_one({"uuid": application_id}, {"app_logs": 1})
        if "app_logs" in app:
            return app["app_logs"]
        else:
            return None


# Choose which database implementation to use
def get_database() -> AbstractDatabaseConn:
    if MONGO_URI:
        logger.info({"timestamp": datetime.now().isoformat(), "msg": "initalizing MONGO DATABASE...", "data": f"with {MONGO_URI}"})
        return MongoDatabaseConn()
    else:
        logger.info({"timestamp": datetime.now().isoformat(), "msg": "IN-MEMORY DATABASE initialized. Ready to use!", "data": ""})
        return InMemoryDatabaseConn()

# Instantiate the database connection
database = get_database()
