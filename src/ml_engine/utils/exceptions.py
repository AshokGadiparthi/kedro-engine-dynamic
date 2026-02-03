"""Custom exceptions for ML Engine."""

class MLEngineException(Exception):
    """Base exception for ML Engine."""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"

class DataValidationError(MLEngineException):
    """Raised when data validation fails."""
    pass

class DataCleaningError(MLEngineException):
    """Raised when data cleaning fails."""
    pass

class DataLoadingError(MLEngineException):
    """Raised when data loading fails."""
    pass

class InsufficientDataError(MLEngineException):
    """Raised when dataset too small."""
    pass
