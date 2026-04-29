from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status

from alpr_stms_shared.constants import (
    ROLE_COMPLAINT_OFFICER,
    ROLE_SYSTEM_ADMIN,
    ROLE_TRAFFIC_OFFICER,
)
from app.auth.dependencies import require_roles, require_user


def _user(role_code: str):
    return SimpleNamespace(role=SimpleNamespace(code=role_code))


def test_require_user_redirects_when_anonymous() -> None:
    with pytest.raises(HTTPException) as exc:
        require_user(current_user=None)
    assert exc.value.status_code == status.HTTP_303_SEE_OTHER
    assert exc.value.headers == {"Location": "/auth/login"}


def test_require_user_returns_authenticated_user() -> None:
    user = _user(ROLE_TRAFFIC_OFFICER)
    assert require_user(current_user=user) is user


def test_require_roles_allows_matching_role() -> None:
    dependency = require_roles(ROLE_SYSTEM_ADMIN, ROLE_COMPLAINT_OFFICER)
    user = _user(ROLE_SYSTEM_ADMIN)
    assert dependency(current_user=user) is user


def test_require_roles_forbids_other_roles() -> None:
    dependency = require_roles(ROLE_SYSTEM_ADMIN)
    user = _user(ROLE_TRAFFIC_OFFICER)
    with pytest.raises(HTTPException) as exc:
        dependency(current_user=user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
