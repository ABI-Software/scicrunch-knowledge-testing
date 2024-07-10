import unittest
import requests
import json
import boto3
import botocore
import urllib.parse
import os
import re

from urllib.parse import urljoin

from tests.config import Config
from tests.slow_tests.manifest_name_to_discover_name import name_map, biolucida_name_map

pennsieve_cache = {}
name_mapping = {}
doc_link = 'https://github.com/ABI-Software/scicrunch-knowledge-testing/tree/doc_v1'

s3 = boto3.client(
    "s3",
    aws_access_key_id=Config.AWS_KEY,
    aws_secret_access_key=Config.AWS_SECRET,
    region_name="us-east-1",
)

S3_BUCKET_NAME = "prd-sparc-discover50-use1"

NOT_SPECIFIED = 'not-specified'

def get_datasets(start, size):

    headers = {'accept': 'application/json'}
    params = {'api_key': Config.SCICRUNCH_API_KEY}

    scicrunch_host = Config.SCICRUNCH_API_HOST + '/'

    scicrunch_request = {
        "from": start,
        "size": size,
        "_source": [
            "item.curie",
            "item.name",
            "item.types",
            "objects.biolucida",
            "objects.additional_mimetype",
            "objects.mimetype",
            "objects.dataset",
            "pennsieve.version",
            "pennsieve.identifier",
            "pennsieve.uri"
        ]
    }

    return requests.post(urljoin(scicrunch_host, '_search?preference=abiknowledgetesting'), json=scicrunch_request, params=params, headers=headers)

def extract_bucket_name(original_name):
    return original_name.split('/')[2]

def test_segmentation_s3file(id, version, obj, bucket):
    file_path = None

    mime_type = obj['additional_mimetype']['name']
    scicrunch_path = obj['dataset']['path']
    if "files/" not in scicrunch_path:
        file_path = "files/" + scicrunch_path
        scicrunch_path = "files/" + scicrunch_path
    else:
        file_path = scicrunch_path
    if file_path in name_map:
        file_path = name_map[file_path]
    file_path = f'{id}/' + file_path

    try:
        head_response = s3.head_object(
            Bucket=bucket,
            Key=file_path,
            RequestPayer="requester"
        )
        if head_response and 'ResponseMetadata' in head_response and 200 == head_response['ResponseMetadata']['HTTPStatusCode']:
            pass
        else:
            return {
                'Mimetype': mime_type,
                'Path': file_path,
                'Reason': 'Invalid response',
            }
    except botocore.exceptions.ClientError as error:
        return {
            'Mimetype': mime_type,
            'Path': file_path,
            'Reason': f"{error}",
        }
    return None

#Test object to check for any possible error
def test_segmentation_thumbnail(id, version, obj, bucket):
    global pennsieve_cache
    global name_mapping
    error_response = None
    pennsieve_path = None
    file_path = None
    name_difference = {}

    try:
        scicrunch_path = obj['dataset']['path']
        if "files/" not in scicrunch_path:
            file_path = "files/" + scicrunch_path
            scicrunch_path = "files/" + scicrunch_path
        else:
            file_path = scicrunch_path
        # Map name for path
        if file_path in name_map:
            file_path = name_map[file_path]

        query_args = [
            ('datasetId', id), 
            ('version', version), 
            ('path', file_path)
        ]
        url = f"{Config.NEUROLUCIDA_HOST}/thumbnail"
        response = requests.get(url, params=query_args)
        if response.status_code == 200:
            return
        error_response = {
            'NeuroLucidaPath': scicrunch_path,
            'Reason': 'Cannot get a valid request from NeuroLucida',
        }
        
        folderPath = file_path.rsplit("/", 1)[0]
        files = []
        if folderPath in pennsieve_cache:
            files = pennsieve_cache[folderPath]
        else:
            file_url = '{api}/datasets/{id}/versions/{version}/files/browse?path={folderPath}'.format( 
                api=Config.PENNSIEVE_API_HOST, id=id, version=version, folderPath=folderPath)
            file_response = requests.get(file_url)
            files_info = file_response.json()
            if 'files' in files_info:
                files = files_info['files']

        if len(files) > 0:
            pennsieve_cache[folderPath] = files
            file_path_match = False
            s3file_path = None
            for local_file in files:
                # Only check segmentation files
                if local_file['fileType'] == 'XML':
                    scicrunch_filename = scicrunch_path.rsplit("/", 1)[1]
                    # In case minor difference exists between scicrunch and s3 filename
                    # Usually filename should match with each other, file path may not
                    scicrunch_modified = ' '.join(re.findall('[.a-zA-Z0-9]+', scicrunch_filename)).rsplit(".", 1)[0]
                    local_modified = ' '.join(re.findall('[.a-zA-Z0-9]+', local_file['name'])).rsplit(".", 1)[0]
                    if local_file['name'] == scicrunch_filename or scicrunch_modified in local_modified or local_modified in scicrunch_modified:
                        s3file_path = local_file['uri'].replace(f's3://{bucket}/{id}/', '')
                        # Compare Scicrunch file path with S3 file path mainly the file name
                        if scicrunch_path == s3file_path:
                            file_path_match = True
                            break
                        else:
                            name_difference = {
                                'scicrunch': scicrunch_filename, 
                                's3': s3file_path.rsplit("/", 1)[1]
                            }
                
            if not file_path_match:
                if len(name_difference) > 0:
                    error_response['Detail'] = f'Possibly inconsistency between Scicrunch and S3: {str(name_difference)}.'
                    if id not in name_mapping:
                        name_mapping[id] = {}
                    name_mapping[id][scicrunch_path] = s3file_path
            else:
                error_response['Detail'] = 'File path is matched. Possibly no thumbnail for this file.'
        else:
            error_response['Detail'] = 'Folder path cannot be found on Pennsieve. Please check the path.'

    except Exception as e:
        error_response = {
            'NeuroLucidaPath': scicrunch_path,
            'Reason': str(e),
        }

    return error_response

def test_segmentation_list(id, version, obj_list, bucket):
    global pennsieve_cache
    SegmentationFound = False
    SEGMENTATION_FILES = [
        'application/vnd.mbfbioscience.metadata+xml', 
        'application/vnd.mbfbioscience.neurolucida+xml'
    ]
    objectErrors = []

    for obj in obj_list:
        mime_type = obj.get('additional_mimetype', NOT_SPECIFIED)
        if mime_type != NOT_SPECIFIED:
            mime_type = mime_type.get('name')
        if not mime_type:
            mime_type = obj['mimetype'].get('name', NOT_SPECIFIED)

        if mime_type in SEGMENTATION_FILES:
            SegmentationFound = True
            error = test_segmentation_thumbnail(id, version, obj, bucket)
            error2 = test_segmentation_s3file(id, version, obj, bucket)
            if error:
                objectErrors.append(error)
            if error2:
                objectErrors.append(error2)

    numberOfErrors = len(objectErrors)
    fileReports = {
        'Total': numberOfErrors,
        'Objects': objectErrors
    }
    return {"FileReports": fileReports, "SegmentationFound": SegmentationFound}
                
#Test the dataset 
def test_datasets_information(dataset):
    report = {
        'Id': 'none',
        'DOI': 'none',
        '_id': dataset['_id'],
        'Errors': [],
        'ObjectErrors': {'Total': 0, 'Objects':[]}
    }
    if '_source' in dataset :
        source = dataset['_source']
        if 'item' in source:
            report['Name'] = source['item'].get('name', 'none')
            report['DOI'] = source['item'].get('curie', 'none')

        if 'pennsieve' in source and 'version' in source['pennsieve'] and 'identifier' in source['pennsieve']:
            id = source['pennsieve']['identifier']
            version = source['pennsieve']['version']['identifier']
            report['Id'] = id
            report['Version'] = version
            bucket = S3_BUCKET_NAME
            if 'uri' in source['pennsieve']:
                bucket = extract_bucket_name(source['pennsieve']['uri'])
            if version:
                obj_list = source['objects'] if 'objects' in source else []
                obj_reports = test_segmentation_list(id, version, obj_list, bucket)
                report['ObjectErrors'] = obj_reports['FileReports']
                report['Segmentation'] = obj_reports['SegmentationFound']
            else:
                report['Errors'].append('Missing version')
    return report


class SegmentationDatasetFilesTest(unittest.TestCase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def test_files_information(self):
        global name_mapping
        start = 0
        size = 20
        keepGoing = True
        totalSize = 0
        reportOutput = 'reports/segmentation_reports.json'
        nameMappingOutput = 'reports/segmentation_name_mapping.json'
        reports = {'Tested': 0, 'Failed': 0, 'FailedIds':[], 'Datasets':[]}
        testSize = 2000
        totalSegmentation = 0

        # '''
        # Test selected datasets
        # '''
        # scicrunch_datasets = open('reports/scicrunch_datasets.json')
        # datasets = json.load(scicrunch_datasets)
        # scicrunch_datasets.close()
        # dataset_list = list(datasets.keys())
        # # dataset_list = [
        # #     '221'
        # # ]

        # '''
        # Add datasets to the queue
        # '''
        # data = {'hits': {'hits': []}}
        # for dataset_id in dataset_list:
        #     data['hits']['hits'].append(datasets[dataset_id])

        # for dataset in data['hits']['hits']:
        #     report = test_datasets_information(dataset)
        #     if 'Segmentation' in report and report['Segmentation']:
        #         totalSegmentation = totalSegmentation + 1
        #     print(f"Reports generated for {report['Id']}")
        #     if len(report['Errors']) > 0 or report['ObjectErrors']['Total'] > 0:
        #         reports['FailedIds'].append(report['Id'])
        #         reports['Datasets'].append(report)

        # totalSize = totalSize + len(data['hits']['hits'])

        '''
        Test all the datasets
        '''
        while keepGoing :
            scicrunch_response = get_datasets(start, size)
            self.assertEqual(200, scicrunch_response.status_code)

            data = scicrunch_response.json()

            #No more result, stop
            if size > len(data['hits']['hits']):
                keepGoing = False

            #keepGoing= False

            start = start + size

            for dataset in data['hits']['hits']:
                report = test_datasets_information(dataset)
                if 'Segmentation' in report and report['Segmentation']:
                    totalSegmentation = totalSegmentation + 1
                print(f"Reports generated for {report['Id']}")
                if len(report['Errors']) > 0 or report['ObjectErrors']['Total'] > 0:
                    reports['FailedIds'].append(report['Id'])
                    reports['Datasets'].append(report)

            totalSize = totalSize + len(data['hits']['hits'])

            if totalSize >= testSize:
                keepGoing = False

        # Generate the report
        reports['Tested'] = totalSize
        reports['Tested Datasets with Segmentation'] = totalSegmentation
        print(f"Number of datasets tested: {reports['Tested']}")
        reports['Failed'] = len(reports['FailedIds'])
        print(f"Number of dataset with erros: {reports['Failed']}")
        if reports['Failed'] > 0:
            print(f"Failed Datasets: {reports['FailedIds']}")
            
        os.makedirs(os.path.dirname(reportOutput), exist_ok=True)
        with open(reportOutput, 'w') as outfile:
            json.dump(reports, outfile, indent=4)
        
        os.makedirs(os.path.dirname(nameMappingOutput), exist_ok=True)
        with open(nameMappingOutput, 'w') as outfile:
            json.dump(name_mapping, outfile, indent=4)
    
        print(f"Full report has been generated at {reportOutput}")

        self.assertEqual(0, len(reports['FailedIds']))

if __name__ == '__main__':
    unittest.main()
