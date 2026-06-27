import re
import math
import string
from collections import Counter
from typing import Dict, List, Tuple, Optional

try:
    import zxcvbn
    HAS_ZXCVBN = True
except ImportError:
    HAS_ZXCVBN = False

class PasswordAnalyzer:
    COMMON_PASSWORDS = {
        "123456", "password", "123456789", "12345", "12345678", "qwerty",
        "abc123", "password1", "1234", "111111", "123123", "admin",
        "letmein", "welcome", "monkey", "dragon", "master", "hello",
        "fuckyou", "666666", "1234567", "sunshine", "princess", "iloveyou",
        "charlie", "justin", "freedom", "whatever", "trustno1", "batman",
        "qwertyuiop", "123qwe", "1q2w3e", "qwerty123", "1234567890",
        "qazwsx", "password123", "mypassword", "pass123", "123321",
        "qwerty1", "qwertyui", "123456a", "abc123!", "password!",
        "123abc", "qwerty12345", "1q2w3e4r", "zxcvbn", "qwerty123456",
        "12345678910", "password1234", "123456789a", "a123456", "123456789q",
        "qwertyuiopasdfghjklzxcvbnm", "1qaz2wsx", "11111111", "000000",
        "1234567890qwerty", "1234567890password", "passwordpassword",
        "qwertyqwerty", "abc123456", "1234567890!", "1234567890-",
        "qwerty123!", "qwerty12345!", "1q2w3e4r5t", "1234567890q",
        "password1!", "password123!", "admin123", "letmein123",
        "welcome123", "monkey123", "dragon123", "master123", "hello123",
        "fuckyou123", "66666666", "sunshine123", "princess123",
        "iloveyou123", "charlie123", "justin123", "freedom123",
        "whatever123", "trustno123", "batman123"
    }
    COMMON_WORDS = {
        "password", "admin", "user", "login", "welcome", "hello", "monkey",
        "dragon", "master", "sunshine", "princess", "iloveyou", "charlie",
        "justin", "freedom", "whatever", "trust", "batman", "qwerty",
        "abc", "letmein", "shadow", "ashley", "baseball", "football",
        "soccer", "hockey", "basketball", "tennis", "golf", "swimming",
        "running", "jumping", "coding", "programming", "python", "java",
        "javascript", "linux", "windows", "apple", "orange", "banana",
        "star", "moon", "sun", "cloud", "rain", "snow", "wind", "fire",
        "water", "earth", "sky", "blue", "red", "green", "yellow",
        "black", "white", "purple", "orange", "pink", "brown", "grey",
        "gold", "silver", "copper", "iron", "steel", "wood", "stone",
        "city", "town", "country", "world", "planet", "galaxy", "universe",
        "science", "math", "history", "art", "music", "movie", "book",
        "computer", "internet", "network", "security", "cyber", "hack",
        "attack", "defense", "firewall", "encryption", "key", "lock",
        "safe", "vault", "secret", "private", "public", "hidden"
    }

    @classmethod
    def analyze(cls, password: str) -> Dict:
        if not password:
            return cls._empty_result()
        result = {
            'password': password,
            'length': len(password),
            'has_upper': any(c.isupper() for c in password),
            'has_lower': any(c.islower() for c in password),
            'has_digits': any(c.isdigit() for c in password),
            'has_special': any(c in string.punctuation for c in password),
            'repeated_chars': cls._check_repeated(password),
            'sequential_chars': cls._check_sequential(password),
            'keyboard_pattern': cls._check_keyboard(password),
            'dictionary_word': cls._check_dictionary(password),
            'common_password': password.lower() in cls.COMMON_PASSWORDS,
            'entropy_bits': cls._shannon_entropy(password),
            'recommendations': [],
            'zxcvbn': None
        }
        if HAS_ZXCVBN:
            zx_result = zxcvbn.zxcvbn(password)
            result['zxcvbn'] = {
                'score': zx_result['score'],
                'crack_time_seconds': zx_result['crack_times_seconds']['offline_slow_hashing_1e4_per_second'],
                'crack_time_display': zx_result['crack_times_display']['offline_slow_hashing_1e4_per_second'],
                'feedback': zx_result['feedback'],
                'guesses': zx_result['guesses']
            }
            zx_mapped = zx_result['score'] * 25
        else:
            zx_mapped = None
        custom_score = cls._compute_custom_score(result)
        final_score = int(0.6 * custom_score + 0.4 * zx_mapped) if zx_mapped is not None else custom_score
        final_score = max(0, min(100, final_score))
        result['strength_score'] = final_score
        result['strength_level'] = cls._score_to_level(final_score)
        if HAS_ZXCVBN:
            result['estimated_crack_time_seconds'] = result['zxcvbn']['crack_time_seconds']
            result['estimated_crack_time_display'] = result['zxcvbn']['crack_time_display']
        else:
            entropy = result['entropy_bits']
            guesses = 2 ** entropy if entropy > 0 else 1
            crack_seconds = guesses / 1e10
            result['estimated_crack_time_seconds'] = crack_seconds
            result['estimated_crack_time_display'] = cls._format_crack_time(crack_seconds)
        result['recommendations'] = cls._generate_recommendations(result)
        entropy = result['entropy_bits']
        has_patterns = any([
            result['repeated_chars'],
            result['sequential_chars'],
            result['keyboard_pattern'],
            result['dictionary_word'],
            result['common_password']
        ])
        result['randomness'] = entropy > 40 and not has_patterns
        result['predictability'] = not result['randomness']
        return result

    @staticmethod
    def _empty_result() -> Dict:
        return {
            'password': '',
            'length': 0,
            'has_upper': False,
            'has_lower': False,
            'has_digits': False,
            'has_special': False,
            'repeated_chars': False,
            'sequential_chars': False,
            'keyboard_pattern': False,
            'dictionary_word': False,
            'common_password': False,
            'entropy_bits': 0.0,
            'strength_score': 0,
            'strength_level': 'Very Weak',
            'estimated_crack_time_seconds': 0,
            'estimated_crack_time_display': 'Instant',
            'recommendations': ['Please enter a password.'],
            'randomness': False,
            'predictability': True,
            'zxcvbn': None
        }

    @staticmethod
    def _shannon_entropy(password: str) -> float:
        if not password:
            return 0.0
        freq = Counter(password)
        length = len(password)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def _check_repeated(password: str) -> bool:
        for i in range(len(password) - 1):
            if password[i] == password[i+1]:
                return True
        return False

    @staticmethod
    def _check_sequential(password: str) -> bool:
        if len(password) < 3:
            return False
        for i in range(len(password) - 2):
            a, b, c = password[i], password[i+1], password[i+2]
            if a.isdigit() and b.isdigit() and c.isdigit():
                if (ord(b) == ord(a) + 1 and ord(c) == ord(b) + 1) or \
                   (ord(b) == ord(a) - 1 and ord(c) == ord(b) - 1):
                    return True
            if a.isalpha() and b.isalpha() and c.isalpha():
                if (ord(b) == ord(a) + 1 and ord(c) == ord(b) + 1) or \
                   (ord(b) == ord(a) - 1 and ord(c) == ord(b) - 1):
                    return True
        return False

    @staticmethod
    def _check_keyboard(password: str) -> bool:
        lower = password.lower()
        patterns = [
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "qwerty", "asdf", "zxcv", "qwertyui", "asdfgh", "zxcvbn",
            "qwert", "asdfg", "zxc", "qwertyuiopasdfghjklzxcvbnm"
        ]
        for pat in patterns:
            if pat in lower or pat[::-1] in lower:
                return True
        return False

    @staticmethod
    def _check_dictionary(password: str) -> bool:
        lower = password.lower()
        for word in PasswordAnalyzer.COMMON_WORDS:
            if word in lower:
                return True
        return False

    @staticmethod
    def _compute_custom_score(result: Dict) -> int:
        score = 0
        length = result['length']
        if length >= 12:
            score += 25
        elif length >= 10:
            score += 20
        elif length >= 8:
            score += 15
        elif length >= 6:
            score += 10
        else:
            score += 5
        variety = 0
        if result['has_upper']:
            variety += 7
        if result['has_lower']:
            variety += 7
        if result['has_digits']:
            variety += 8
        if result['has_special']:
            variety += 8
        score += min(30, variety)
        penalties = 0
        if result['repeated_chars']:
            penalties += 10
        if result['sequential_chars']:
            penalties += 15
        if result['keyboard_pattern']:
            penalties += 20
        if result['dictionary_word']:
            penalties += 25
        if result['common_password']:
            penalties += 30
        entropy = result['entropy_bits']
        if entropy >= 60:
            score += 20
        elif entropy >= 50:
            score += 15
        elif entropy >= 40:
            score += 10
        elif entropy >= 30:
            score += 5
        score = max(0, score - penalties)
        return min(100, score)

    @staticmethod
    def _score_to_level(score: int) -> str:
        if score >= 80:
            return 'Very Strong'
        elif score >= 60:
            return 'Strong'
        elif score >= 40:
            return 'Moderate'
        elif score >= 20:
            return 'Weak'
        return 'Very Weak'

    @staticmethod
    def _format_crack_time(seconds: float) -> str:
        if seconds < 1:
            return 'Instant'
        elif seconds < 60:
            return f'{int(seconds)} seconds'
        elif seconds < 3600:
            return f'{int(seconds/60)} minutes'
        elif seconds < 86400:
            return f'{int(seconds/3600)} hours'
        elif seconds < 31536000:
            return f'{int(seconds/86400)} days'
        elif seconds < 1e9:
            return f'{int(seconds/31536000)} years'
        return 'Centuries'

    @staticmethod
    def _generate_recommendations(result: Dict) -> List[str]:
        recs = []
        if result['length'] < 8:
            recs.append('Use at least 8 characters.')
        elif result['length'] < 12:
            recs.append('Consider using 12 or more characters for stronger security.')
        if not result['has_upper']:
            recs.append('Add uppercase letters.')
        if not result['has_lower']:
            recs.append('Add lowercase letters.')
        if not result['has_digits']:
            recs.append('Add numbers.')
        if not result['has_special']:
            recs.append('Add special characters (e.g. !@#$%^&*).')
        if result['repeated_chars']:
            recs.append('Avoid repeated consecutive characters.')
        if result['sequential_chars']:
            recs.append('Avoid sequential letters or numbers (e.g. "abc", "123").')
        if result['keyboard_pattern']:
            recs.append('Avoid keyboard patterns (e.g. "qwerty", "asdf").')
        if result['dictionary_word']:
            recs.append('Avoid using common dictionary words.')
        if result['common_password']:
            recs.append('This password is on the list of most common passwords. Choose a unique one.')
        if HAS_ZXCVBN and result['zxcvbn']:
            zx_feedback = result['zxcvbn']['feedback']
            if zx_feedback.get('warning'):
                recs.append(zx_feedback['warning'])
            if zx_feedback.get('suggestions'):
                recs.extend(zx_feedback['suggestions'])
        seen = set()
        unique_recs = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique_recs.append(r)
        return unique_recs