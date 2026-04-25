"""Local config view for the auth module.

Reads from the global `Settings`. Add auth-specific env vars (refresh-token TTL,
password policy, etc.) here as the domain grows.
"""

from app.core.config import settings

__all__ = ["settings"]
