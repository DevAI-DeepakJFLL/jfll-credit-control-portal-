"""
Credit Appraisal Parser facade.
Re-exports from backend.app.automations.credit_appraisal.parser for backward compatibility.
"""
from backend.app.automations.credit_appraisal.parser import *
from backend.app.automations.credit_appraisal.parser import (
    _normalize_date,
    _format_inr
)
