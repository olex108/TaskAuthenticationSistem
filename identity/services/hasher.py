from pwdlib import PasswordHash


class PasswordHasher:
    password_hash: PasswordHash = PasswordHash.recommended()
    DUMMY_HASH: str = password_hash.hash("dummypassword")

    @classmethod
    def verify_password(cls, plain_password, hashed_password) -> bool:
        return cls.password_hash.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password) -> str:
        return cls.password_hash.hash(password)

    @classmethod
    def dammy_verify(cls, password) -> bool:
        cls.verify_password(password, cls.DUMMY_HASH)
        return False
