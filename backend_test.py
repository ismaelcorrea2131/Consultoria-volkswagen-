#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Volkswagen Consortium API
Tests all critical endpoints according to test_result.md requirements
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from frontend/.env
BACKEND_URL = "https://188ecdf9-c8d1-47b5-a532-0da620ba65c7.preview.emergentagent.com/api"

class VWConsortiumAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
        
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Volkswagen Consortium API" in data.get("message", ""):
                    self.log_test("API Root", True, f"API is running - {data['message']}")
                    return True
                else:
                    self.log_test("API Root", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_lead_creation(self):
        """Test lead creation with valid Brazilian data"""
        lead_data = {
            "name": "Carlos Eduardo Silva",
            "whatsapp": "(91) 99876-5432",
            "city": "Belém",
            "model": "Golf GTI",
            "source": "hero-form"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/leads", json=lead_data)
            if response.status_code == 200:
                data = response.json()
                # Verify response structure
                required_fields = ["id", "name", "whatsapp", "city", "model", "source", "status", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Verify UUID format
                    try:
                        uuid.UUID(data["id"])
                        self.log_test("Lead Creation", True, f"Lead created successfully with ID: {data['id']}")
                        return True, data["id"]
                    except ValueError:
                        self.log_test("Lead Creation", False, f"Invalid UUID format: {data['id']}")
                        return False, None
                else:
                    self.log_test("Lead Creation", False, f"Missing fields: {missing_fields}")
                    return False, None
            else:
                self.log_test("Lead Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("Lead Creation", False, f"Error: {str(e)}")
            return False, None
    
    def test_get_leads(self):
        """Test retrieving all leads"""
        try:
            response = self.session.get(f"{self.base_url}/leads")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Leads", True, f"Retrieved {len(data)} leads")
                    return True
                else:
                    self.log_test("Get Leads", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Get Leads", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Leads", False, f"Error: {str(e)}")
            return False
    
    def test_lead_stats(self):
        """Test lead statistics endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/leads/stats")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total", "new", "contacted", "converted", "by_source"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Lead Stats", True, f"Stats retrieved - Total: {data['total']}, New: {data['new']}")
                    return True
                else:
                    self.log_test("Lead Stats", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Lead Stats", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Lead Stats", False, f"Error: {str(e)}")
            return False
    
    def test_get_cars(self):
        """Test retrieving cars data - should return 4 VW models"""
        try:
            response = self.session.get(f"{self.base_url}/cars")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check for expected VW models
                    expected_models = ["Golf GTI", "Polo Track", "T-Cross", "Nivus"]
                    found_models = [car.get("model", "") for car in data]
                    
                    # Verify all expected models are present
                    missing_models = [model for model in expected_models if model not in found_models]
                    
                    if not missing_models and len(data) >= 4:
                        # Check Brazilian pricing format
                        pricing_valid = all("R$" in car.get("monthly_price", "") for car in data)
                        if pricing_valid:
                            self.log_test("Get Cars", True, f"Retrieved {len(data)} cars with all expected VW models and Brazilian pricing")
                            return True
                        else:
                            self.log_test("Get Cars", False, "Some cars missing Brazilian pricing format (R$)")
                            return False
                    else:
                        self.log_test("Get Cars", False, f"Missing expected models: {missing_models}. Found: {found_models}")
                        return False
                else:
                    self.log_test("Get Cars", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Get Cars", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Cars", False, f"Error: {str(e)}")
            return False
    
    def test_get_testimonials(self):
        """Test retrieving testimonials - should return 3 testimonials from Pará state"""
        try:
            response = self.session.get(f"{self.base_url}/testimonials")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check for Pará cities
                    para_cities = ["Belém", "Ananindeua", "Castanhal"]
                    testimonial_cities = [t.get("city", "") for t in data]
                    
                    # Verify testimonials are from Pará
                    para_testimonials = [t for t in data if any(city in t.get("city", "") for city in para_cities)]
                    
                    if len(para_testimonials) >= 3:
                        # Check required fields
                        required_fields = ["name", "city", "car", "testimonial", "rating", "contemplated"]
                        valid_structure = all(all(field in t for field in required_fields) for t in data)
                        
                        if valid_structure:
                            self.log_test("Get Testimonials", True, f"Retrieved {len(data)} testimonials from Pará state")
                            return True
                        else:
                            self.log_test("Get Testimonials", False, "Some testimonials missing required fields")
                            return False
                    else:
                        self.log_test("Get Testimonials", False, f"Expected testimonials from Pará cities, found cities: {testimonial_cities}")
                        return False
                else:
                    self.log_test("Get Testimonials", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Get Testimonials", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Testimonials", False, f"Error: {str(e)}")
            return False
    
    def test_get_blog_posts(self):
        """Test retrieving blog posts - should return 3 educational articles in Portuguese"""
        try:
            response = self.session.get(f"{self.base_url}/blog/posts")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) >= 3:
                        # Check for Portuguese content and consortium-related topics
                        required_fields = ["title", "excerpt", "slug", "category", "read_time", "published_at"]
                        valid_structure = all(all(field in post for field in required_fields) for post in data)
                        
                        # Check for consortium-related content (Portuguese keywords)
                        consortium_keywords = ["consórcio", "contemplação", "financiamento", "carta de crédito"]
                        has_consortium_content = any(
                            any(keyword in post.get("title", "").lower() or keyword in post.get("excerpt", "").lower() 
                                for keyword in consortium_keywords)
                            for post in data
                        )
                        
                        if valid_structure and has_consortium_content:
                            self.log_test("Get Blog Posts", True, f"Retrieved {len(data)} educational articles with consortium content")
                            return True
                        else:
                            issues = []
                            if not valid_structure:
                                issues.append("invalid structure")
                            if not has_consortium_content:
                                issues.append("missing consortium content")
                            self.log_test("Get Blog Posts", False, f"Issues: {', '.join(issues)}")
                            return False
                    else:
                        self.log_test("Get Blog Posts", False, f"Expected at least 3 posts, got {len(data)}")
                        return False
                else:
                    self.log_test("Get Blog Posts", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Get Blog Posts", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Blog Posts", False, f"Error: {str(e)}")
            return False
    
    def test_analytics_endpoints(self):
        """Test basic analytics endpoints"""
        try:
            # Test analytics dashboard
            response = self.session.get(f"{self.base_url}/analytics/dashboard")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_leads", "total_page_views", "total_form_interactions"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Analytics Dashboard", True, f"Dashboard data retrieved - Total leads: {data['total_leads']}")
                    return True
                else:
                    self.log_test("Analytics Dashboard", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Analytics Dashboard", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Analytics Dashboard", False, f"Error: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test CORS configuration for frontend integration"""
        try:
            # Make an OPTIONS request to check CORS headers
            response = self.session.options(f"{self.base_url}/cars")
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            present_headers = [header for header in cors_headers if header in response.headers]
            
            if len(present_headers) >= 2:  # At least origin and methods should be present
                self.log_test("CORS Configuration", True, f"CORS headers present: {present_headers}")
                return True
            else:
                self.log_test("CORS Configuration", False, f"Missing CORS headers. Present: {present_headers}")
                return False
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚗 VOLKSWAGEN CONSORTIUM API - BACKEND TESTING")
        print("=" * 60)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Test sequence based on priority
        tests = [
            ("API Connectivity", self.test_api_root),
            ("Lead Creation", lambda: self.test_lead_creation()[0]),  # Only return success status
            ("Get Leads", self.test_get_leads),
            ("Lead Statistics", self.test_lead_stats),
            ("Cars Data", self.test_get_cars),
            ("Testimonials", self.test_get_testimonials),
            ("Blog Posts", self.test_get_blog_posts),
            ("Analytics", self.test_analytics_endpoints),
            ("CORS Headers", self.test_cors_headers)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Backend is ready for frontend integration.")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the issues above.")
            return False

def main():
    """Main test execution"""
    tester = VWConsortiumAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()