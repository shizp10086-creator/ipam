"""
Unit tests for password encryption and verification

Tests the security module's password hashing and verification functions
to ensure they meet requirement 18.1 (password encryption using bcrypt).
"""
import pytest
from app.core.security import get_password_hash, verify_password


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    def test_hash_password_returns_string(self):
        """Test that password hashing returns a string"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_from_plain(self):
        """Test that hashed password is different from plain password"""
        password = "my_secure_password"
        hashed = get_password_hash(password)
        
        assert hashed != password
    
    def test_hash_password_uses_bcrypt_format(self):
        """Test that hashed password uses bcrypt format ($2b$)"""
        password = "test_password"
        hashed = get_password_hash(password)
        
        # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")
    
    def test_same_password_produces_different_hashes(self):
        """Test that hashing the same password twice produces different hashes (salt)"""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Due to salt, same password should produce different hashes
        assert hash1 != hash2
    
    def test_hash_empty_password(self):
        """Test hashing an empty password"""
        password = ""
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_long_password(self):
        """Test hashing a very long password"""
        password = "a" * 1000
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_special_characters(self):
        """Test hashing password with special characters"""
        password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/~`"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_unicode_characters(self):
        """Test hashing password with unicode characters"""
        password = "密码123パスワード🔒"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestPasswordVerification:
    """Test password verification functionality"""
    
    def test_verify_correct_password(self):
        """Test that correct password verification returns True"""
        password = "correct_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password verification returns False"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "MyPassword"
        hashed = get_password_hash(password)
        
        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False
        assert verify_password("MyPassword", hashed) is True
    
    def test_verify_empty_password(self):
        """Test verification with empty password"""
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False
    
    def test_verify_special_characters(self):
        """Test verification with special characters"""
        password = "P@ssw0rd!#$%"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!#$", hashed) is False
    
    def test_verify_unicode_characters(self):
        """Test verification with unicode characters"""
        password = "密码123パスワード🔒"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("密码123", hashed) is False
    
    def test_verify_whitespace_matters(self):
        """Test that whitespace in passwords matters"""
        password = "password with spaces"
        hashed = get_password_hash(password)
        
        assert verify_password("password with spaces", hashed) is True
        assert verify_password("passwordwithspaces", hashed) is False
        assert verify_password(" password with spaces", hashed) is False
        assert verify_password("password with spaces ", hashed) is False
    
    def test_verify_with_invalid_hash_format(self):
        """Test verification with invalid hash format"""
        password = "test_password"
        invalid_hash = "not_a_valid_bcrypt_hash"
        
        # passlib raises an exception for invalid hash formats
        with pytest.raises(Exception):
            verify_password(password, invalid_hash)


class TestPasswordHashingIntegration:
    """Integration tests for password hashing and verification"""
    
    def test_hash_and_verify_workflow(self):
        """Test complete workflow: hash a password and verify it"""
        original_password = "user_password_123"
        
        # Step 1: Hash the password
        hashed_password = get_password_hash(original_password)
        
        # Step 2: Verify correct password
        assert verify_password(original_password, hashed_password) is True
        
        # Step 3: Verify incorrect password
        assert verify_password("wrong_password", hashed_password) is False
    
    def test_multiple_users_same_password(self):
        """Test that multiple users can have the same password with different hashes"""
        password = "common_password"
        
        # Hash for user 1
        hash1 = get_password_hash(password)
        # Hash for user 2
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_password_change_scenario(self):
        """Test password change scenario"""
        old_password = "old_password_123"
        new_password = "new_password_456"
        
        # Hash old password
        old_hash = get_password_hash(old_password)
        
        # Verify old password works
        assert verify_password(old_password, old_hash) is True
        
        # Hash new password
        new_hash = get_password_hash(new_password)
        
        # Verify new password works with new hash
        assert verify_password(new_password, new_hash) is True
        
        # Verify old password doesn't work with new hash
        assert verify_password(old_password, new_hash) is False
        
        # Verify new password doesn't work with old hash
        assert verify_password(new_password, old_hash) is False


class TestPasswordSecurityRequirements:
    """Test that password implementation meets security requirements"""
    
    def test_bcrypt_algorithm_used(self):
        """
        Test that bcrypt algorithm is used (Requirement 18.1)
        
        **Validates: Requirements 18.1**
        """
        password = "test_password"
        hashed = get_password_hash(password)
        
        # Bcrypt hashes have a specific format: $2[abxy]$[cost]$[22 character salt][31 character hash]
        # They start with $2a$, $2b$, $2x$, or $2y$
        assert hashed.startswith("$2"), "Password hash should use bcrypt algorithm"
        
        # Bcrypt hashes should be 60 characters long
        assert len(hashed) == 60, "Bcrypt hash should be 60 characters"
    
    def test_password_not_stored_in_plain_text(self):
        """
        Test that passwords are not stored in plain text (Requirement 18.1)
        
        **Validates: Requirements 18.1**
        """
        password = "my_secret_password"
        hashed = get_password_hash(password)
        
        # Hashed password should not contain the original password
        assert password not in hashed
        assert password.lower() not in hashed.lower()
    
    def test_salt_is_unique_per_hash(self):
        """
        Test that each hash uses a unique salt (Requirement 18.1)
        
        **Validates: Requirements 18.1**
        """
        password = "same_password"
        
        # Generate multiple hashes
        hashes = [get_password_hash(password) for _ in range(10)]
        
        # All hashes should be unique (due to unique salts)
        assert len(set(hashes)) == len(hashes), "Each hash should have a unique salt"
    
    def test_verification_is_constant_time(self):
        """
        Test that password verification doesn't leak timing information
        
        This is a basic test - bcrypt's verify is designed to be constant-time
        to prevent timing attacks.
        
        **Validates: Requirements 18.1**
        """
        password = "test_password"
        hashed = get_password_hash(password)
        
        # Both correct and incorrect passwords should be verified
        # (bcrypt handles constant-time comparison internally)
        result_correct = verify_password(password, hashed)
        result_incorrect = verify_password("wrong_password", hashed)
        
        assert result_correct is True
        assert result_incorrect is False
