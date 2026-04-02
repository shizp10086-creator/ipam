"""
Property-based tests for password encryption and verification

Uses Hypothesis to test password hashing and verification across a wide range
of inputs to ensure the implementation is robust and meets requirement 18.1.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from app.core.security import get_password_hash, verify_password


# Strategy for generating valid passwords
# Use simpler strategy to avoid timeout issues with complex unicode
password_strategy = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),  # Exclude surrogates and control characters
        min_codepoint=32,  # Start from space character
        max_codepoint=1000  # Limit to common unicode range
    ),
    min_size=0,
    max_size=50  # Reduced from 100 to speed up tests
)


class TestPasswordHashingProperties:
    """Property-based tests for password hashing"""
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_always_returns_string(self, password):
        """
        Property: For any password, hashing returns a non-empty string
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_uses_bcrypt_format(self, password):
        """
        Property: For any password, the hash uses bcrypt format
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        # Bcrypt hashes start with $2a$, $2b$, $2x$, or $2y$
        assert hashed.startswith("$2")
        # Bcrypt hashes are always 60 characters
        assert len(hashed) == 60
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_different_from_plain(self, password):
        """
        Property: For any password, the hash is different from the plain password
        
        **Validates: Requirements 18.1**
        """
        # Skip very short passwords that might accidentally match part of hash
        assume(len(password) > 0)
        
        hashed = get_password_hash(password)
        
        assert hashed != password
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_same_password_different_hashes(self, password):
        """
        Property: For any password, hashing twice produces different results (unique salt)
        
        **Validates: Requirements 18.1**
        """
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to unique salt, hashes should be different
        assert hash1 != hash2
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_is_deterministic_for_verification(self, password):
        """
        Property: For any password, the hash can be used to verify the original password
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        # The original password should verify against its hash
        assert verify_password(password, hashed) is True


class TestPasswordVerificationProperties:
    """Property-based tests for password verification"""
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_correct_password_always_verifies(self, password):
        """
        Property: For any password, verification with correct password returns True
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    @given(
        password=password_strategy,
        wrong_password=password_strategy
    )
    @settings(max_examples=30)
    def test_different_password_fails_verification(self, password, wrong_password):
        """
        Property: For any two different passwords, verification fails
        
        **Validates: Requirements 18.1**
        """
        # Only test when passwords are actually different
        assume(password != wrong_password)
        
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_verification_is_idempotent(self, password):
        """
        Property: For any password, verification can be called multiple times with same result
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        # Verify multiple times
        result1 = verify_password(password, hashed)
        result2 = verify_password(password, hashed)
        result3 = verify_password(password, hashed)
        
        # All results should be the same
        assert result1 == result2 == result3 == True


class TestPasswordHashingInvariants:
    """Test invariants that should always hold for password hashing"""
    
    @given(
        password1=password_strategy,
        password2=password_strategy
    )
    @settings(max_examples=30)
    def test_hash_collision_resistance(self, password1, password2):
        """
        Property: Different passwords should produce different hashes (collision resistance)
        
        Note: Due to salting, even the same password produces different hashes,
        so different passwords will definitely produce different hashes.
        
        **Validates: Requirements 18.1**
        """
        # Only test when passwords are different
        assume(password1 != password2)
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        # Hashes should be different
        assert hash1 != hash2
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_is_one_way(self, password):
        """
        Property: For any password, it should be computationally infeasible to
        reverse the hash back to the original password
        
        This is a basic test - we verify that the hash doesn't contain the password.
        
        **Validates: Requirements 18.1**
        """
        assume(len(password) > 0)
        
        hashed = get_password_hash(password)
        
        # The hash should not contain the original password
        assert password not in hashed
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_hash_length_is_constant(self, password):
        """
        Property: For any password, the hash length is constant (60 characters for bcrypt)
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        # Bcrypt hashes are always 60 characters
        assert len(hashed) == 60


class TestPasswordSecurityProperties:
    """Property-based tests for security requirements"""
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_no_plaintext_leakage(self, password):
        """
        Property: For any password, the hash should not leak the plaintext
        
        **Validates: Requirements 18.1**
        """
        assume(len(password) > 3)  # Skip very short passwords
        
        hashed = get_password_hash(password)
        
        # Hash should not contain recognizable parts of the password
        # (for passwords longer than 3 characters)
        if len(password) > 3:
            # Check that no substring of length > 3 appears in the hash
            for i in range(len(password) - 3):
                substring = password[i:i+4]
                assert substring not in hashed
    
    @given(
        password=st.text(min_size=1, max_size=30),
        num_hashes=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=20)
    def test_unique_salts(self, password, num_hashes):
        """
        Property: For any password, multiple hashes should all be unique (unique salts)
        
        **Validates: Requirements 18.1**
        """
        hashes = [get_password_hash(password) for _ in range(num_hashes)]
        
        # All hashes should be unique
        assert len(set(hashes)) == len(hashes)
    
    @given(password=password_strategy)
    @settings(max_examples=30)
    def test_verification_returns_boolean(self, password):
        """
        Property: For any password and hash, verification returns a boolean
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        
        assert isinstance(result, bool)
        assert result in [True, False]


class TestPasswordEdgeCases:
    """Property-based tests for edge cases"""
    
    @given(password=st.text(min_size=0, max_size=0))
    @settings(max_examples=5)
    def test_empty_password_handling(self, password):
        """
        Property: Empty passwords can be hashed and verified
        
        **Validates: Requirements 18.1**
        """
        assert password == ""
        
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 60
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False
    
    @given(password=st.text(min_size=100, max_size=200))
    @settings(max_examples=10)
    def test_long_password_handling(self, password):
        """
        Property: Long passwords can be hashed and verified
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 60
        assert verify_password(password, hashed) is True
    
    @given(password=st.text(alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'S', 'Zs'),
        min_codepoint=33,
        max_codepoint=126
    ), min_size=1, max_size=50))
    @settings(max_examples=30)
    def test_special_characters_handling(self, password):
        """
        Property: Passwords with special characters can be hashed and verified
        
        **Validates: Requirements 18.1**
        """
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
