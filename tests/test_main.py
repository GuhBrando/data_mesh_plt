import unittest
from backend.main import app


class TestMain(unittest.TestCase):

    def test_app_is_fastapi(self):
        from fastapi import FastAPI
        self.assertIsInstance(app, FastAPI)


if __name__ == '__main__':
    unittest.main()
