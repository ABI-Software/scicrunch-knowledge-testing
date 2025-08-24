import unittest
import os
import subprocess
import shutil
import requests
import pytest

ENDPOINTS = [
    'https://mapcore-demo.org/staging/flatmap/v1/',
    'https://mapcore-demo.org/current/flatmap/v3/'
]

FLATMAPS = [
    'human-flatmap_male',
    'human-flatmap_female',
    'rat-flatmap'
]

def set_variables(endpoint, data):
    os.environ["TARGET_END_POINT"] = endpoint + 'competency/query'
    for key, value in data.items():
        if key == 'human-flatmap_male':
            os.environ["LATEST_MALE_UUID"] = value['uuid']
            os.environ["LATEST_SCKAN_VERSION"] = value['knowledge-source']
        elif key == 'human-flatmap_female':
            os.environ["LATEST_FEMALE_UUID"] = value['uuid']
        elif key == 'rat-flatmap':
            os.environ["LATEST_RAT_UUID"] = value['uuid']

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
        for endpoint in ENDPOINTS:
            flatmap_info = get_flatmap_info(endpoint)
            latest_flatmap = get_latest_flatmap(flatmap_info, FLATMAPS)
            set_variables(endpoint, latest_flatmap)
            # Run all tests inside their repo
            subprocess.run(["pytest", "external/flatmap-server/tests/"], env=os.environ)

if __name__ == '__main__':
    unittest.main()
