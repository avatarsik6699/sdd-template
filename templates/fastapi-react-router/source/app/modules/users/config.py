"""Local config view for the users module.

Add user-specific env vars (default page size, password policy thresholds, etc.)
here as the domain grows. For now this is a placeholder that re-exports the global
settings so callers within the module have a single import target.
"""

from app.core.config import settings

__all__ = ["settings"]
