#!/usr/bin/env python3
"""
Integration Test Suite for AURELIUS API
Tests all major endpoints and functionality
"""

import requests
import json
import time
from typing import Optional, Dict

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"

class APITester:
    """Integration tester for AURELIUS API"""

    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.email = f"test_{int(time.time())}@example.com"
        self.password = "TestPass123!"
        self.name = "Test User"
        self.tests_passed = 0
        self.tests_failed = 0

    def _print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if details:
            print(f"  → {details}")
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to API"""
        url = f"{API_BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{API_V1_URL}/{endpoint}"

        if self.token and "headers" not in kwargs:
            kwargs["headers"] = {"Authorization": f"Bearer {self.token}"}

        try:
            response = getattr(self.session, method.lower())(url, **kwargs)
            return {
                "status": response.status_code,
                "data": response.json() if response.text else None,
                "response": response
            }
        except Exception as e:
            print(f"  ⚠️  Request error: {e}")
            return None

    # Test 1: Health Check
    def test_health(self):
        """Test API health endpoint"""
        result = self._make_request("GET", "/health")
        passed = result and result["status"] == 200
        self._print_test(
            "Health Check",
            passed,
            f"Status: {result['status'] if result else 'Error'}"
        )
        return passed

    # Test 2: User Registration
    def test_register(self):
        """Test user registration"""
        payload = {
            "email": self.email,
            "password": self.password,
            "name": self.name
        }

        result = self._make_request("POST", "/auth/register", json=payload)

        if result and result["status"] == 200:
            data = result["data"]
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            passed = bool(self.token and self.user_id)
            self._print_test(
                "User Registration",
                passed,
                f"User: {self.email}, Token received: {bool(self.token)}"
            )
            return passed
        else:
            self._print_test(
                "User Registration",
                False,
                f"Status: {result['status'] if result else 'Error'}"
            )
            return False

    # Test 3: User Login (with new user)
    def test_login(self):
        """Test user login"""
        # Create a new test user
        test_email = f"login_test_{int(time.time())}@example.com"
        test_password = "LoginTest123!"

        # Register
        register_payload = {
            "email": test_email,
            "password": test_password,
            "name": "Login Test User"
        }
        self._make_request("POST", "/auth/register", json=register_payload)

        # Login
        login_payload = {
            "email": test_email,
            "password": test_password
        }

        result = self._make_request("POST", "/auth/login", json=login_payload)

        passed = result and result["status"] == 200 and result["data"].get("access_token")
        self._print_test(
            "User Login",
            passed,
            f"User: {test_email}, Token received: {bool(result and result['data'].get('access_token'))}"
        )
        return passed

    # Test 4: Token Verification
    def test_verify_token(self):
        """Test token verification"""
        if not self.token:
            self._print_test("Token Verification", False, "No token available")
            return False

        result = self._make_request("GET", "/auth/verify")

        email = result["data"].get("user", {}).get("email") if result and result["status"] == 200 else None
        passed = result and result["status"] == 200 and email
        self._print_test(
            "Token Verification",
            passed,
            f"Email verified: {email if email else 'Error'}"
        )
        return passed

    # Test 5: Strategy Generation
    def test_generate_strategies(self):
        """Test strategy generation endpoint"""
        if not self.token:
            self._print_test("Strategy Generation", False, "Not authenticated")
            return False

        payload = {
            "goal": "Create a momentum-based trading strategy",
            "risk_preference": "moderate",
            "max_strategies": 3
        }

        result = self._make_request("POST", "/api/v1/strategies/generate", json=payload)

        if result and result["status"] == 200:
            data = result["data"]
            strategy_count = len(data.get("strategies", []))
            passed = strategy_count > 0
            self._print_test(
                "Strategy Generation",
                passed,
                f"Generated {strategy_count} strategies"
            )
            return passed
        else:
            self._print_test(
                "Strategy Generation",
                False,
                f"Status: {result['status'] if result else 'Error'}"
            )
            return False

    # Test 6: List Strategies
    def test_list_strategies(self):
        """Test listing strategies"""
        if not self.token:
            self._print_test("List Strategies", False, "Not authenticated")
            return False

        result = self._make_request("GET", "/api/v1/strategies/?skip=0&limit=10")

        if result and result["status"] == 200:
            data = result["data"]
            total = data.get("total", 0)
            passed = total >= 0
            self._print_test(
                "List Strategies",
                passed,
                f"Total strategies: {total}"
            )
            return passed
        else:
            self._print_test(
                "List Strategies",
                False,
                f"Status: {result['status'] if result else 'Error'}"
            )
            return False

    # Test 7: Run Backtest
    def test_run_backtest(self):
        """Test backtest execution"""
        if not self.token:
            self._print_test("Run Backtest", False, "Not authenticated")
            return False

        # First, generate a strategy to get a valid strategy ID
        gen_payload = {
            "goal": "Create a simple momentum strategy",
            "risk_preference": "moderate",
            "max_strategies": 1
        }

        gen_result = self._make_request("POST", "/api/v1/strategies/generate", json=gen_payload)
        if not gen_result or gen_result["status"] != 200:
            self._print_test("Run Backtest", False, "Failed to generate strategy for backtest")
            return False

        strategy_id = gen_result["data"]["strategies"][0]["id"]

        # Now run backtest with the real strategy ID
        payload = {
            "strategy_id": strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10000,
            "instruments": ["SPY"]
        }

        result = self._make_request("POST", "/api/v1/backtests/run", json=payload)

        if result and result["status"] == 200:
            data = result["data"]
            backtest_id = data.get("backtest_id")
            passed = bool(backtest_id)
            self._print_test(
                "Run Backtest",
                passed,
                f"Backtest ID: {backtest_id}"
            )
            return passed
        else:
            self._print_test(
                "Run Backtest",
                False,
                f"Status: {result['status'] if result else 'Error'}"
            )
            return False

    # Test 8: WebSocket Connection
    def test_websocket(self):
        """Test WebSocket endpoint availability"""
        if not self.token:
            self._print_test("WebSocket Connection", False, "Not authenticated")
            return False

        try:
            import websockets
            import asyncio

            async def test_ws():
                try:
                    uri = f"ws://127.0.0.1:8000/ws?token={self.token}"
                    async with websockets.connect(uri) as websocket:
                        # Should receive connection confirmation
                        msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(msg)
                        return data.get("event") == "connected"
                except Exception as e:
                    print(f"  ⚠️  WebSocket error: {e}")
                    return False

            passed = asyncio.run(test_ws())
            self._print_test(
                "WebSocket Connection",
                passed,
                "Connected and received confirmation" if passed else "Connection failed"
            )
            return passed
        except ImportError:
            self._print_test(
                "WebSocket Connection",
                False,
                "websockets library not installed"
            )
            return False

    # Test 9: Authentication Headers
    def test_auth_headers(self):
        """Test that authentication is required"""
        result = self._make_request("GET", "/api/v1/strategies/", headers={})
        # Should fail without token or succeed with 401
        passed = result and result["status"] in [401, 400]
        self._print_test(
            "Authentication Required",
            passed,
            f"Status: {result['status'] if result else 'Error'} (expected 401)"
        )
        return passed

    # Test 10: Invalid Token
    def test_invalid_token(self):
        """Test with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        result = self._make_request("GET", "/auth/verify", headers=headers)

        passed = result and result["status"] in [401, 403]
        self._print_test(
            "Invalid Token Rejection",
            passed,
            f"Status: {result['status'] if result else 'Error'} (expected 401/403)"
        )
        return passed

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*60)
        print("AURELIUS API Integration Test Suite")
        print("="*60 + "\n")

        # Run tests in order
        tests = [
            ("Health Check", self.test_health),
            ("User Registration", self.test_register),
            ("User Login", self.test_login),
            ("Token Verification", self.test_verify_token),
            ("Strategy Generation", self.test_generate_strategies),
            ("List Strategies", self.test_list_strategies),
            ("Run Backtest", self.test_run_backtest),
            ("WebSocket Connection", self.test_websocket),
            ("Authentication Required", self.test_auth_headers),
            ("Invalid Token Rejection", self.test_invalid_token),
        ]

        for name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self._print_test(name, False, f"Exception: {str(e)}")

        # Print summary
        print("\n" + "="*60)
        print(f"Test Results: {self.tests_passed} passed, {self.tests_failed} failed")
        print("="*60 + "\n")

        return self.tests_failed == 0


if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
