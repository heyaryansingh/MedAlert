"""
Structured logging utility for MedAlert backend.
Provides consistent logging across all modules with HIPAA-safe patient data handling.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import json


class StructuredLogger:
    """
    Structured logger with automatic PII redaction for healthcare compliance.
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually __name__ of the module)
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create console handler with formatting
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)

            # JSON-structured format for easy parsing
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @staticmethod
    def _redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact potentially sensitive patient information.

        Args:
            data: Dictionary that may contain PII

        Returns:
            Redacted dictionary safe for logging
        """
        pii_fields = {
            "patient_name",
            "patient_id",
            "email",
            "phone",
            "address",
            "ssn",
            "medical_record_number",
            "date_of_birth",
        }

        redacted = data.copy()
        for field in pii_fields:
            if field in redacted:
                # Keep first 3 chars for debugging, redact rest
                value = str(redacted[field])
                if len(value) > 3:
                    redacted[field] = value[:3] + "***"
                else:
                    redacted[field] = "***"

        return redacted

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message with optional structured data."""
        if extra:
            extra = self._redact_pii(extra)
            message = f"{message} | {json.dumps(extra)}"
        self.logger.info(message)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with optional structured data and exception info."""
        if extra:
            extra = self._redact_pii(extra)
            message = f"{message} | {json.dumps(extra)}"
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message with optional structured data."""
        if extra:
            extra = self._redact_pii(extra)
            message = f"{message} | {json.dumps(extra)}"
        self.logger.warning(message)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message with optional structured data."""
        if extra:
            extra = self._redact_pii(extra)
            message = f"{message} | {json.dumps(extra)}"
        self.logger.debug(message)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message with optional structured data."""
        if extra:
            extra = self._redact_pii(extra)
            message = f"{message} | {json.dumps(extra)}"
        self.logger.critical(message)


class AuditLogger:
    """
    Specialized logger for healthcare audit trails.
    Tracks access to patient data and system actions.
    """

    def __init__(self):
        self.logger = StructuredLogger("medalert.audit", level=logging.INFO)

    def log_access(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log access to protected healthcare information.

        Args:
            user_id: ID of user performing action
            action: Action taken (read, write, delete, etc.)
            resource_type: Type of resource accessed (patient, image, chat)
            resource_id: ID of specific resource
            status: success or failure
            details: Additional context
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
        }

        if details:
            audit_entry["details"] = details

        self.logger.info(f"AUDIT: {action} {resource_type}", extra=audit_entry)

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: Optional[float] = None,
    ):
        """
        Log API endpoint access.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            user_id: Authenticated user ID if applicable
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
        """
        api_entry = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
        }

        if user_id:
            api_entry["user_id"] = user_id

        if response_time_ms:
            api_entry["response_time_ms"] = response_time_ms

        self.logger.info(f"API: {method} {endpoint}", extra=api_entry)


# Global logger instances
def get_logger(name: str) -> StructuredLogger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Singleton audit logger
audit_logger = AuditLogger()
