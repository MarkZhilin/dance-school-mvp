import os
import sys
import tempfile
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "app", "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from db import create_client, init_db, search_clients_by_name


class SearchClientsByNameTests(unittest.TestCase):
    def test_search_clients_by_name_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.sqlite")
            init_db(db_path)
            create_client(
                db_path,
                full_name="Анна",
                phone="+70000000000",
                tg_user_id=None,
                tg_username=None,
                birth_date=None,
                comment=None,
            )

            results_lower = search_clients_by_name(db_path, "анна")
            results_upper = search_clients_by_name(db_path, "АННА")

            self.assertEqual(len(results_lower), 1)
            self.assertEqual(len(results_upper), 1)
            self.assertEqual(results_lower[0][1], "Анна")
            self.assertEqual(results_upper[0][1], "Анна")


if __name__ == "__main__":
    unittest.main()
