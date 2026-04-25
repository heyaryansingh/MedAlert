"""
Data encryption utilities for sensitive health information.
Implements AES-256 encryption with secure key management.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional


class HealthDataEncryption:
    """Encrypt and decrypt sensitive health data using Fernet (AES-256)."""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption with master key.

        Args:
            master_key: Master encryption key (32-byte base64 string).
                       If None, generates a new key.
        """
        if master_key:
            self.key = master_key.encode()
        else:
            self.key = Fernet.generate_key()

        self.cipher = Fernet(self.key)

    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: User password
            salt: Salt for key derivation (16 bytes). If None, generates new salt.

        Returns:
            Derived key (32 bytes, base64 encoded)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Base64 encoded encrypted data
        """
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted plain text

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing sensitive data
            fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))

        return encrypted_data

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()

        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except ValueError:
                    # Field might not be encrypted - leave as is
                    pass

        return decrypted_data


# Sensitive fields that should always be encrypted
SENSITIVE_HEALTH_FIELDS = [
    "ssn",
    "medical_record_number",
    "diagnosis",
    "prescription",
    "lab_results",
    "genetic_data",
    "mental_health_notes",
]


def encrypt_patient_data(patient_data: dict, encryption_key: str) -> dict:
    """
    Encrypt sensitive patient data fields.

    Args:
        patient_data: Patient data dictionary
        encryption_key: Encryption key

    Returns:
        Patient data with encrypted sensitive fields
    """
    encryptor = HealthDataEncryption(encryption_key)
    return encryptor.encrypt_dict(patient_data, SENSITIVE_HEALTH_FIELDS)


def decrypt_patient_data(encrypted_data: dict, encryption_key: str) -> dict:
    """
    Decrypt sensitive patient data fields.

    Args:
        encrypted_data: Encrypted patient data dictionary
        encryption_key: Encryption key

    Returns:
        Patient data with decrypted sensitive fields
    """
    encryptor = HealthDataEncryption(encryption_key)
    return encryptor.decrypt_dict(encrypted_data, SENSITIVE_HEALTH_FIELDS)
