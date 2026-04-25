"""Integration tests for /api/v1/auth/* endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import create_access_token, hash_password
from app.modules.users import User, UserRole


@pytest.fixture()
async def admin_user(db_session: AsyncSession) -> User:
    from uuid import uuid4

    unique = uuid4().hex[:8]
    user = User(
        email=f"test_admin_{unique}@example.com",
        hashed_password=hash_password("testpass123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    return {"Authorization": f"Bearer {token}"}


async def test_login_success(client: AsyncClient, admin_user: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "testpass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, admin_user: User) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "any"},
    )
    assert resp.status_code == 401


async def test_me_with_valid_token(
    client: AsyncClient, admin_user: User, admin_headers: dict
) -> None:
    resp = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == admin_user.email
    assert data["role"] == "admin"
    assert data["is_active"] is True


async def test_me_without_token(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_logout_with_valid_token(client: AsyncClient, admin_headers: dict) -> None:
    resp = await client.post("/api/v1/auth/logout", headers=admin_headers)
    assert resp.status_code == 200


async def test_logout_without_token(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401
