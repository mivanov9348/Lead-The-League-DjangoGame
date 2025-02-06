from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings

def get_cipher():
    key = settings.FERNET_SECRET_KEY
    if not key:
        raise ValueError("FERNET_SECRET_KEY is not set in settings.")
    return Fernet(key)


def encrypt_message(message):
    cipher = get_cipher()
    return cipher.encrypt(message.encode()).decode()

def decrypt_message(encrypted_message):
    if not encrypted_message:
        return ""
    cipher = get_cipher()
    try:
        return cipher.decrypt(encrypted_message.encode()).decode()
    except InvalidToken:
        return "[Decryption Error]"

