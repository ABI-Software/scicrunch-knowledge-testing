import unittest
import os
import subprocess
import shutil
import pytest
from tests.slow_tests.competency_query_utility import get_flatmap_info, get_latest_flatmap, set_variables

class CompetencyQueryTest(unittest.TestCase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def test_competency_query(self):
        # Clone the repo into external/flatmap-server
        repo_path = "external/flatmap-server"
        if not os.path.exists(repo_path):
            subprocess.run(
                ["git", "clone", "https://github.com/AnatomicMaps/flatmap-server.git", repo_path],
                check=True
            )
        else:
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
        # Replace your modified utility file into place
        shutil.copyfile(
            "tests/slow_tests/overrides/utility.py",
            "external/flatmap-server/tests/utility.py"
        )
        exit_code = pytest.main(["external/flatmap-server/tests/"])
        flatmap_info = get_flatmap_info()
        latest_flatmap = get_latest_flatmap(flatmap_info)
        set_variables(latest_flatmap)
        print(f"Pytest exit code: {exit_code}")

if __name__ == '__main__':
    unittest.main()
