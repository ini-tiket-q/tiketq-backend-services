#!/usr/bin/env python3
"""
RBAC Test Script for Auth Service
Tests role-based access control functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000/auth"

def test_rbac():
    print("Testing RBAC (Role-Based Access Control)...")
    
    # Test data
    admin_user = {
        "email": "admin@example.com",
        "password": "adminpass123",
        "role": "admin"
    }
    
    regular_user = {
        "email": "user@example.com",
        "password": "userpass123",
        "role": "user"
    }
    
    try:
        # Test 1: Register admin user
        print("\n1. Registering admin user...")
        response = requests.post(f"{BASE_URL}/register", json=admin_user)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print("Admin user registered successfully")
        else:
            print(f"Error: {response.text}")
            return
        
        # Test 2: Register regular user
        print("\n2. Registering regular user...")
        response = requests.post(f"{BASE_URL}/register", json=regular_user)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            print("Regular user registered successfully")
        else:
            print(f"Error: {response.text}")
            return
        
        # Test 3: Login as admin
        print("\n3. Logging in as admin...")
        login_data = {
            "username": admin_user["email"],
            "password": admin_user["password"]
        }
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print("Admin login successful")
        else:
            print(f"Error: {response.text}")
        
        # Test 4: Login as regular user
        print("\n4. Logging in as regular user...")
        login_data = {
            "username": regular_user["email"],
            "password": regular_user["password"]
        }
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            print("User login successful")
        else:
            print(f"Error: {response.text}")
        
        # Test 5: Admin accessing /me endpoint
        print("\n5. Admin accessing /me endpoint...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"Admin user info: {json.dumps(user_data, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 6: Regular user accessing /me endpoint
        print("\n6. Regular user accessing /me endpoint...")
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"Regular user info: {json.dumps(user_data, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 7: Admin accessing /users endpoint (should succeed)
        print("\n7. Admin accessing /users endpoint...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"Admin can list all users: {len(users)} users found")
        else:
            print(f"Error: {response.text}")
        
        # Test 8: Regular user accessing /users endpoint (should fail)
        print("\n8. Regular user accessing /users endpoint (should fail)...")
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 403:
            print("Correctly denied access to regular user")
        else:
            print(f"Unexpected response: {response.text}")
        
        # Test 9: Admin updating user role
        print("\n9. Admin updating user role...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.put(f"{BASE_URL}/users/2/role?role=admin", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            updated_user = response.json()
            print(f"User role updated: {json.dumps(updated_user, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 10: Regular user trying to update role (should fail)
        print("\n10. Regular user trying to update role (should fail)...")
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.put(f"{BASE_URL}/users/1/role?role=user", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 403:
            print("Correctly denied access to regular user")
        else:
            print(f"Unexpected response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to auth-service. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rbac() 