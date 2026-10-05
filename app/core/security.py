import bcrypt
import secrets
import string

def hash_password(password: str) -> str:
    """Hashes a plaintext password using native bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_secure_password(length: int = 8) -> str:
    """Generates a cryptographically secure random password for student accounts.
    Format: Alphanumeric characters with at least one uppercase, one lowercase, one digit.
    Example: 'X7kP9mQ2'
    Guaranteed not predictable.
    """
    if length < 8:
        length = 8

    # Ensure at least one upper, lower, digit
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    alphabet = upper + lower + digits

    password_chars = [
        secrets.choice(upper),
        secrets.choice(lower),
        secrets.choice(digits),
    ]

    for _ in range(length - 3):
        password_chars.append(secrets.choice(alphabet))

    # Shuffle cryptographically using SystemRandom
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)
