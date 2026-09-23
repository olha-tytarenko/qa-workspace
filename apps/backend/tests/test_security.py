from app.core.security import hash_password, verify_password

# A non-BMP character (an emoji, U+1F600) so backend/frontend password-length
# handling can be proven consistent: Python's `len()` counts it as one code
# point, while JS's `.length` would count it as two UTF-16 code units.
NON_BMP_PASSWORD = "correct-horse-battery" + "\U0001f600"


def test_hash_password_produces_an_argon2id_hash() -> None:
    hashed = hash_password("a sufficiently long password")

    assert hashed.startswith("$argon2id$")
    assert hashed != "a sufficiently long password"


def test_verify_password_accepts_the_matching_password() -> None:
    hashed = hash_password("a sufficiently long password")

    assert verify_password("a sufficiently long password", hashed) is True


def test_verify_password_rejects_a_different_password() -> None:
    hashed = hash_password("a sufficiently long password")

    assert verify_password("a different password entirely", hashed) is False


def test_hash_and_verify_round_trip_a_password_with_a_non_bmp_character() -> None:
    hashed = hash_password(NON_BMP_PASSWORD)

    assert verify_password(NON_BMP_PASSWORD, hashed) is True
    assert len(NON_BMP_PASSWORD) == 22  # Python counts the emoji as one code point.
