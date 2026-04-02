#!/usr/bin/env python3
"""
Verification script for password encryption and verification implementation

This script verifies that task 3.1 (password encryption and verification) is correctly implemented.
It tests the core functionality required by requirement 18.1.
"""

from app.core.security import get_password_hash, verify_password


def test_basic_functionality():
    """Test basic password hashing and verification"""
    print("Testing basic password hashing and verification...")
    
    # Test 1: Hash a password
    password = "test_password_123"
    hashed = get_password_hash(password)
    print(f"✓ Password hashed successfully")
    print(f"  Original: {password}")
    print(f"  Hashed: {hashed}")
    
    # Test 2: Verify correct password
    assert verify_password(password, hashed), "Failed to verify correct password"
    print(f"✓ Correct password verified successfully")
    
    # Test 3: Verify incorrect password
    assert not verify_password("wrong_password", hashed), "Incorrectly verified wrong password"
    print(f"✓ Incorrect password rejected successfully")
    
    # Test 4: Verify bcrypt format
    assert hashed.startswith("$2"), "Hash doesn't use bcrypt format"
    assert len(hashed) == 60, "Hash length is not 60 characters (bcrypt standard)"
    print(f"✓ Hash uses bcrypt format ($2x$ prefix, 60 characters)")
    
    # Test 5: Verify unique salts
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    assert hash1 != hash2, "Same password produced identical hashes (salt not unique)"
    print(f"✓ Unique salts verified (same password produces different hashes)")
    
    # Test 6: Test with special characters
    special_password = "P@ssw0rd!#$%^&*()"
    special_hashed = get_password_hash(special_password)
    assert verify_password(special_password, special_hashed), "Failed with special characters"
    print(f"✓ Special characters handled correctly")
    
    # Test 7: Test with unicode characters
    unicode_password = "密码123パスワード"
    unicode_hashed = get_password_hash(unicode_password)
    assert verify_password(unicode_password, unicode_hashed), "Failed with unicode characters"
    print(f"✓ Unicode characters handled correctly")
    
    # Test 8: Test case sensitivity
    case_password = "MyPassword"
    case_hashed = get_password_hash(case_password)
    assert verify_password("MyPassword", case_hashed), "Failed exact match"
    assert not verify_password("mypassword", case_hashed), "Not case sensitive"
    assert not verify_password("MYPASSWORD", case_hashed), "Not case sensitive"
    print(f"✓ Case sensitivity verified")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print("\nTask 3.1 Implementation Summary:")
    print("- Password hashing using bcrypt: ✓ IMPLEMENTED")
    print("- Password verification function: ✓ IMPLEMENTED")
    print("- Requirement 18.1 compliance: ✓ VERIFIED")
    print("\nThe password encryption and verification functionality is")
    print("correctly implemented and ready for use in the authentication system.")


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        exit(1)
