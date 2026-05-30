from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class EncryptionService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY is not configured")
        self._fernet = Fernet(settings.encryption_key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt credential") from exc


def get_encryption_service() -> EncryptionService:
    return EncryptionService()
