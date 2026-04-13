import pytest

from user_service import UserService


def test_set_subscription_raises_for_unknown_user(monkeypatch):
    service = UserService()
    monkeypatch.setattr(service, "get_user_by_id", lambda _user_id: None)

    with pytest.raises(ValueError, match="User not found"):
        service.set_subscription("missing-user", {"product_id": "monthly"})
