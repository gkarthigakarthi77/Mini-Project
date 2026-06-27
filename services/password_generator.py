import secrets
import string

class PasswordGenerator:
    SIMILAR_CHARS = 'il1Lo0O'
    AMBIGUOUS_CHARS = '{}[]()/\'"`~,;:.<>'

    @classmethod
    def generate(cls, length: int = 16,
                 use_upper: bool = True,
                 use_lower: bool = True,
                 use_numbers: bool = True,
                 use_symbols: bool = True,
                 exclude_similar: bool = False,
                 exclude_ambiguous: bool = False) -> str:
        if length < 4:
            raise ValueError('Password length must be at least 4.')
        pool = ''
        if use_upper:
            pool += string.ascii_uppercase
        if use_lower:
            pool += string.ascii_lowercase
        if use_numbers:
            pool += string.digits
        if use_symbols:
            pool += string.punctuation
        if not pool:
            raise ValueError('At least one character type must be selected.')
        if exclude_similar:
            for ch in cls.SIMILAR_CHARS:
                pool = pool.replace(ch, '')
        if exclude_ambiguous:
            for ch in cls.AMBIGUOUS_CHARS:
                pool = pool.replace(ch, '')
        if not pool:
            raise ValueError('After exclusions, no characters remain. Adjust options.')
        password_chars = [secrets.choice(pool) for _ in range(length)]
        return ''.join(password_chars)