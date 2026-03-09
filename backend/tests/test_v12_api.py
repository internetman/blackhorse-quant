import os
import sys
import unittest

from fastapi.testclient import TestClient


CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402


class V12ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.token_u1 = cls._login("laowang", "laowang123")
        cls.token_u2 = cls._login("dali", "dali123")

    @classmethod
    def _login(cls, username: str, password: str) -> str:
        response = cls.client.post("/api/auth/login/", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        data = response.json()
        return data["token"]

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_watchlist_user_isolation(self):
        response = self.client.get("/api/watchlist/", headers=self._auth_headers(self.token_u2))
        self.assertEqual(response.status_code, 200, response.text)
        items = response.json()
        self.assertGreater(len(items), 0)
        self.assertTrue(all(item["userId"] == "u2" for item in items))

    def test_recommendations_are_aggregated(self):
        response = self.client.get("/api/recommendations/", headers=self._auth_headers(self.token_u1))
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("recommendations", data)
        self.assertGreater(len(data["recommendations"]), 0)

        first = data["recommendations"][0]
        self.assertIn("quote", first)
        self.assertIn("news", first)
        self.assertIn("volume", first["quote"])
        self.assertIsInstance(first["quote"]["volume"], int)
        self.assertIsInstance(first["news"], list)

    def test_quote_symbol_normalization(self):
        response = self.client.get(
            "/api/quote/?symbol=600519",
            headers=self._auth_headers(self.token_u1),
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["symbol"], "600519.SH")

    def test_stock_search_supports_full_pinyin(self):
        response = self.client.get(
            "/api/stocks/search?q=guizhou&limit=10",
            headers=self._auth_headers(self.token_u1),
        )
        self.assertEqual(response.status_code, 200, response.text)
        symbols = {item["symbol"] for item in response.json()}
        self.assertIn("600519.SH", symbols)


if __name__ == "__main__":
    unittest.main()
