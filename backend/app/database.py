"""
Database module for Jet Freight Logistics Credit Control CRM.
Re-exports core database connection and Credit Appraisal data access methods
to ensure 100% backward compatibility across all existing unit tests and callers.
"""
from backend.app.core.database import (
    get_db,
    init_db,
    DB_PATH,
    STORAGE_DIR,
    DEFAULT_STORAGE_DIR,
    is_lambda,
    _db_initialized
)

from backend.app.automations.credit_appraisal.service import (
    get_appraisals_count,
    save_appraisal,
    get_all_appraisals,
    get_appraisal_by_id,
    get_appraisal_by_token_or_id
)

__all__ = [
    "get_db",
    "init_db",
    "DB_PATH",
    "STORAGE_DIR",
    "DEFAULT_STORAGE_DIR",
    "is_lambda",
    "get_appraisals_count",
    "save_appraisal",
    "get_all_appraisals",
    "get_appraisal_by_id",
    "get_appraisal_by_token_or_id"
]
