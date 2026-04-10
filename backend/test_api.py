"""
Quick API Test Script
Tests authentication and basic endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_register():
    """Test user registration"""
    print("Testing user registration...")
    user_data = {
        "email": "test.parent@example.com",
        "password": "testpassword123",
        "full_name": "Test Parent",
        "role": "parent",
        "phone": "+44 7700 900000"
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json() if response.status_code == 201 else None


def test_login(email, password):
    """Test user login"""
    print("Testing user login...")
    login_data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Token: {data['access_token'][:20]}...")
        print(f"User: {data['user']['email']}")
        print()
        return data['access_token']
    else:
        print(f"Error: {response.json()}")
        print()
        return None


def test_get_current_user(token):
    """Test get current user"""
    print("Testing get current user...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_create_student(token):
    """Test create student"""
    print("Testing create student...")
    student_data = {
        "first_name": "Emma",
        "last_name": "Smith",
        "date_of_birth": "2014-05-15",
        "gender": "Female",
        "school_name": "Greenwood Primary",
        "year_group": "Year 5"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/students/", json=student_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print(f"Student created: {response.json()}")
        print()
        return response.json()
    else:
        print(f"Error: {response.json()}")
        print()
        return None


def test_list_students(token):
    """Test list students"""
    print("Testing list students...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/students/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Students: {response.json()}")
    print()


def main():
    """Run all tests"""
    print("="*60)
    print("EdPsych AI Backend - API Tests")
    print("="*60)
    print()

    try:
        # Test health
        test_health_check()

        # Test registration (will fail if user exists - that's ok!)
        test_register()

        # Test login
        token = test_login("test.parent@example.com", "testpassword123")

        if token:
            # Test authenticated endpoints
            test_get_current_user(token)
            student = test_create_student(token)
            test_list_students(token)

            print("="*60)
            print("All tests completed!")
            print("="*60)
        else:
            print("Login failed - check credentials or register first")

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend")
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  python main.py")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
