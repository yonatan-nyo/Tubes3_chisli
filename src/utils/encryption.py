import random
import string
import base64


class CustomEncryption:
    """Custom encryption implementation using multiple techniques"""

    def __init__(self, key: str = "TUBES3_ENCRYPTION_KEY"):
        self.key = key
        self.key_length = len(key)

    def _generate_salt(self, length: int = 8) -> str:
        """Generate random salt for encryption"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _caesar_cipher(self, text: str, shift: int) -> str:
        """Apply Caesar cipher with given shift"""
        result = ""
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                result += chr((ord(char) - ascii_offset + shift) %
                              26 + ascii_offset)
            else:
                result += char
        return result

    def _vigenere_cipher(self, text: str, key: str) -> str:
        """Apply Vigenère cipher"""
        result = ""
        key_index = 0

        for char in text:
            if char.isalpha():
                key_char = key[key_index % len(key)]
                shift = ord(key_char.upper()) - ord('A')

                if char.isupper():
                    result += chr((ord(char) - ord('A') + shift) %
                                  26 + ord('A'))
                else:
                    result += chr((ord(char) - ord('a') + shift) %
                                  26 + ord('a'))

                key_index += 1
            else:
                result += char

        return result

    def _xor_cipher(self, text: str, key: str) -> str:
        """Apply XOR cipher"""
        result = ""
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result += chr(ord(char) ^ ord(key_char))
        return result

    def encrypt(self, plaintext: str) -> str:
        """Encrypt text using layered encryption"""
        if not plaintext:
            return ""

        # Generate salt and prepend to text
        salt = self._generate_salt()
        salted_text = salt + plaintext

        # Layer 1: Caesar cipher with dynamic shift
        shift = sum(ord(c) for c in self.key) % 26
        encrypted = self._caesar_cipher(salted_text, shift)

        # Layer 2: Vigenère cipher
        encrypted = self._vigenere_cipher(encrypted, self.key)

        # Layer 3: XOR cipher
        encrypted = self._xor_cipher(encrypted, self.key)

        # Encode to make it database-safe using standard Base64
        # Convert string to bytes before encoding
        encrypted_bytes = encrypted.encode('utf-8')
        # Use URL-safe Base64 encoding and decode result to a string for DB storage
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt text by reversing encryption layers"""
        if not ciphertext:
            return ""

        try:
            # Decode from base64
            # Convert the Base64 string back to bytes
            encrypted_bytes = base64.urlsafe_b64decode(
                ciphertext.encode('utf-8'))
            # Decode the bytes back to a string
            encrypted = encrypted_bytes.decode('utf-8')

            # Reverse Layer 3: XOR cipher
            decrypted = self._xor_cipher(encrypted, self.key)

            # Reverse Layer 2: Vigenère cipher
            decrypted = self._vigenere_cipher_decrypt(decrypted, self.key)

            # Reverse Layer 1: Caesar cipher
            shift = sum(ord(c) for c in self.key) % 26
            decrypted = self._caesar_cipher(decrypted, -shift)

            # Remove salt (first 8 characters)
            return decrypted[8:]

        except (ValueError, TypeError, base64.binascii.Error):
            # If decryption fails (e.g., not valid Base64), return original
            # This handles cases where unencrypted data might be passed
            return ciphertext

    def _vigenere_cipher_decrypt(self, text: str, key: str) -> str:
        """Decrypt Vigenère cipher"""
        result = ""
        key_index = 0

        for char in text:
            if char.isalpha():
                key_char = key[key_index % len(key)]
                shift = ord(key_char.upper()) - ord('A')

                if char.isupper():
                    result += chr((ord(char) - ord('A') - shift) %
                                  26 + ord('A'))
                else:
                    result += chr((ord(char) - ord('a') - shift) %
                                  26 + ord('a'))

                key_index += 1
            else:
                result += char

        return result


# Global encryption instance
encryption = CustomEncryption()
