import time
from unittest.mock import patch


class TestPasswordHashing:
    """Tests for password hashing utilities"""

    def test_hash_password(self):
        """Test password hashing"""
        from src.core.utility import hash_password

        password = "mySecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes"""
        from src.core.utility import hash_password

        password = "samePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Due to salt, hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from src.core.utility import hash_password, verify_password

        plain = "correctPassword"
        hashed = hash_password(plain)

        assert verify_password(plain, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from src.core.utility import hash_password, verify_password

        plain = "correctPassword"
        hashed = hash_password(plain)

        assert verify_password("wrongPassword", hashed) is False


class TestHashingFunctions:
    """Tests for general hashing utilities"""

    def test_hash_bytes(self):
        """Test hashing bytes"""
        from src.core.utility import hash_bytes

        data = b"test data"
        hashed = hash_bytes(data)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_bytes_same_data_same_hash(self):
        """Test that same bytes produce same hash"""
        from src.core.utility import hash_bytes

        data = b"consistent data"
        hash1 = hash_bytes(data)
        hash2 = hash_bytes(data)

        assert hash1 == hash2

    def test_hash_bytes_different_data_different_hash(self):
        """Test that different bytes produce different hashes"""
        from src.core.utility import hash_bytes

        data1 = b"data one"
        data2 = b"data two"

        hash1 = hash_bytes(data1)
        hash2 = hash_bytes(data2)

        assert hash1 != hash2

    def test_hash_str(self):
        """Test hashing strings"""
        from src.core.utility import hash_str

        text = "test string"
        hashed = hash_str(text)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_str_consistency(self):
        """Test string hashing consistency"""
        from src.core.utility import hash_str

        text = "consistent string"
        hash1 = hash_str(text)
        hash2 = hash_str(text)

        assert hash1 == hash2

    def test_hash_str_special_characters(self):
        """Test hashing strings with special characters"""
        from src.core.utility import hash_str

        text = "special!@#$%^&*()chars"
        hashed = hash_str(text)

        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestTimeUtilities:
    """Tests for time measurement utilities"""

    def test_get_elapsed_time(self):
        """Test elapsed time calculation"""
        from src.core.utility import get_elapsed_time_till_now_in_ms

        start_time = time.perf_counter()
        time.sleep(0.01)  # Sleep for 10ms
        elapsed = get_elapsed_time_till_now_in_ms(start_time)

        # Should be approximately 10ms or more
        assert elapsed >= 10
        assert elapsed < 1000  # Should be less than 1 second

    def test_get_elapsed_time_immediate(self):
        """Test elapsed time with immediate call"""
        from src.core.utility import get_elapsed_time_till_now_in_ms

        start_time = time.perf_counter()
        elapsed = get_elapsed_time_till_now_in_ms(start_time)

        # Should be very small but positive
        assert elapsed >= 0
        assert elapsed < 10


class TestCacheDetails:
    """Tests for CacheDetails data class"""

    def test_cache_details_creation(self, test_db_session):
        """Test creating CacheDetails instance"""
        from src.core.utility import CacheDetails

        details = CacheDetails(user_id=123, question="Test question")

        assert details.user_id == 123
        assert details.question == "Test question"

    def test_cache_details_equality(self, test_db_session):
        """Test CacheDetails equality"""
        from src.core.utility import CacheDetails

        details1 = CacheDetails(user_id=1, question="Q")
        details2 = CacheDetails(user_id=1, question="Q")

        # Should have same attributes
        assert details1.user_id == details2.user_id
        assert details1.question == details2.question


class TestEnvironmentHelpers:
    """Tests for environment and configuration helpers"""

    @patch.dict("os.environ", {"AWS_SAM_LOCAL": "true"})
    def test_aws_sam_local_detection(self):
        """Test detection of AWS SAM local environment"""
        import os

        is_sam_local = os.getenv("AWS_SAM_LOCAL") is not None
        assert is_sam_local is True

    @patch.dict("os.environ", {}, clear=True)
    def test_not_aws_sam_local(self):
        """Test when not in AWS SAM local"""
        import os

        is_sam_local = os.getenv("AWS_SAM_LOCAL") is not None
        assert is_sam_local is False


class TestInputValidation:
    """Tests for input validation and sanitization"""

    def test_hash_empty_bytes(self):
        """Test hashing empty bytes"""
        from src.core.utility import hash_bytes

        empty = b""
        hashed = hash_bytes(empty)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_empty_string(self):
        """Test hashing empty string"""
        from src.core.utility import hash_str

        empty = ""
        hashed = hash_str(empty)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_unicode_string(self):
        """Test hashing unicode strings"""
        from src.core.utility import hash_str

        unicode_text = "Hello 世界 🌍"
        hashed = hash_str(unicode_text)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_password_hash_length(self):
        """Test that password hashes have reasonable length"""
        from src.core.utility import hash_password

        password = "test"
        hashed = hash_password(password)

        # Argon2 hashes are typically 90+ characters
        assert len(hashed) > 50


class TestModelConstants:
    """Tests for model and configuration constants"""

    def test_ai_model_config(self):
        """Test that AI model configuration is accessible"""
        from src.core.constants import settings

        assert settings.OPENAI_MODEL is not None
        assert isinstance(settings.OPENAI_MODEL, str)
        assert len(settings.OPENAI_MODEL) > 0

    def test_response_type_enum(self):
        """Test ResponseType enum"""
        from src.core.constants import ResponseType

        assert hasattr(ResponseType, "SUCCESS")
        assert hasattr(ResponseType, "ERROR")

    def test_model_cost_constants(self):
        """Test that model cost constants exist"""
        from src.core.constants import MODEL_COST_PER_MILLION_TOKENS

        assert isinstance(MODEL_COST_PER_MILLION_TOKENS, dict)
        assert len(MODEL_COST_PER_MILLION_TOKENS) > 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_very_long_password(self):
        """Test hashing very long password"""
        from src.core.utility import hash_password, verify_password

        long_password = "a" * 1000
        hashed = hash_password(long_password)

        assert verify_password(long_password, hashed) is True

    def test_very_long_string_hash(self):
        """Test hashing very long string"""
        from src.core.utility import hash_str

        long_string = "x" * 10000
        hashed = hash_str(long_string)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_binary_data_with_nulls(self):
        """Test hashing binary data containing null bytes"""
        from src.core.utility import hash_bytes

        data_with_nulls = b"test\x00data\x00here"
        hashed = hash_bytes(data_with_nulls)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_whitespace_only_password(self):
        """Test password with only whitespace"""
        from src.core.utility import hash_password, verify_password

        whitespace_pass = "   "
        hashed = hash_password(whitespace_pass)

        assert verify_password(whitespace_pass, hashed) is True
        assert verify_password("", hashed) is False
