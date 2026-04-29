from app.core.security import hash_password, verify_password


def test_password_hash_round_trip() -> None:
    hashed = hash_password("Phase1StrongPassword!")
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password("Phase1StrongPassword!", hashed) is True
    assert verify_password("wrong-password", hashed) is False
