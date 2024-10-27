import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Initial in-memory storage for applications
applications: Dict[str, Dict] = {}

def create_application(application_id: str, data: Dict[str, Any]) -> str:
    """Creates a new application entry in the in-memory storage and returns the application ID."""
    applications[application_id] = data
    return application_id

def get_application(application_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an application by ID, if it exists."""
    return applications.get(application_id)

def delete_application(application_id: str) -> bool:
    """Deletes an application by ID. Returns True if successful, False if not found."""
    if application_id in applications:
        del applications[application_id]
        return True
    return False

def log_application_interaction(application_id: str, log_entry: Dict[str, Any]) -> bool:
    """Logs an interaction to an application's log if the application exists."""
    app = applications.get(application_id)
    if app:
        app["app_logs"].append(log_entry)
        return True
    return False

def get_application_logs(application_id: str) -> Optional[list]:
    """Returns the logs for an application if it exists."""
    app = applications.get(application_id)
    return app["app_logs"] if app else None
