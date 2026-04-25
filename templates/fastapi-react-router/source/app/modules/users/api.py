"""HTTP routes for the users domain.

No public endpoints yet — `/auth/me` lives in the auth module because it's an
authentication concern. Add user-management endpoints here as they're specced.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])
