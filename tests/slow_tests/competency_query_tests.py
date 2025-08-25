import unittest
import os
import subprocess
import shutil
import requests
import pytest
from tests.config import Config

ENDPOINT = Config.FLATMAP_ENDPOINT

FLATMAPS = [
    'human-flatmap_male',
    'human-flatmap_female',
    'rat-flatmap'
]

TESTING_VARIABLES = {}

def get_variables(key):
    return TESTING_VARIABLES[key]

def set_variables(endpoint, data):
    TESTING_VARIABLES["END_POINT"] = endpoint + 'competency/query'
    for key, value in data.items():
        if key == 'human-flatmap_male':
            TESTING_VARIABLES["MALE_UUID"] = value['uuid']
            TESTING_VARIABLES["SCKAN_VERSION"] = value['knowledge-source']
        elif key == 'human-flatmap_female':
            TESTING_VARIABLES["FEMALE_UUID"] = value['uuid']
        elif key == 'rat-flatmap':
            TESTING_VARIABLES["RAT_UUID"] = value['uuid']

def get_latest_flatmap(data, scope):
    latest_flatmap_dict = {}
    for key, value in data.items():
        if key not in latest_flatmap_dict and key in scope:
            stored_maps = sorted(value, key=lambda x: x["created"], reverse=True)
            latest_flatmap_dict[key] = stored_maps[0]
    return latest_flatmap_dict

def get_flatmap_info(endpoint):
    flatmap_dict = {}
    flatmap_response = requests.get(endpoint)
    flatmap_json = flatmap_response.json()
    for map in flatmap_json:
        map_id = map.get('id', 'N/A')
        if map_id not in flatmap_dict:
            flatmap_dict[map_id] = []
        info = {
            'uuid': map.get('uuid', 'N/A'),
            'created': map.get('created', 'N/A'),
            'knowledge-source': map.get('sckan', {}).get('knowledge-source', 'N/A')
        }
        flatmap_dict[map_id].append(info)
    return flatmap_dict

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
            "tests/slow_tests/utility.py",
            "external/flatmap-server/tests/utility.py"
        )
        flatmap_info = get_flatmap_info(ENDPOINT)
        latest_flatmap = get_latest_flatmap(flatmap_info, FLATMAPS)
        set_variables(ENDPOINT, latest_flatmap)
        exit_code = pytest.main(["external/flatmap-server/tests/"])
        print(f"Pytest exit code: {exit_code}")

if __name__ == '__main__':
    unittest.main()
