import unittest

import app


class DashboardApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_dashboard_and_assets_are_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Threat intelligence", response.data)
        response.close()
        response = self.client.get("/app.js")
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_search_returns_matching_reports(self):
        response = self.client.get("/api/reports?q=ransomware")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["total"], 1)
        self.assertIn("ransomware", payload["items"][0]["category"])

    def test_category_filter_is_applied(self):
        response = self.client.get("/api/reports?category=malware")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertTrue(all(item["category"] == "malware" for item in payload["items"]))

    def test_classifier_reports_keyword_signals(self):
        response = self.client.post(
            "/api/classify",
            json={"text": "A ransomware campaign encrypts files and demands extortion payment."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["category"], "ransomware")
        self.assertIn("extortion", response.get_json()["signals"])

    def test_classifier_rejects_empty_text(self):
        response = self.client.post("/api/classify", json={"text": " "})
        self.assertEqual(response.status_code, 400)

    def test_schema_endpoint_reports_bson_sizes(self):
        response = self.client.get("/api/lab/schema")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mode"], "demo")
        self.assertEqual(payload["limitBytes"], 16 * 1024 * 1024)
        self.assertGreater(payload["averageBytes"], 0)
        self.assertLess(payload["maximumBytes"], payload["limitBytes"] * 0.75)


if __name__ == "__main__":
    unittest.main()
