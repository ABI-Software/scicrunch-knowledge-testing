import unittest
import requests
import json
import urllib.parse
import os

from urllib.parse import urljoin

from tests.config import Config

pennsieveCache = {}
doc_link = 'https://github.com/ABI-Software/scicrunch-knowledge-testing/tree/doc_v1'

S3_BUCKET_NAME = "pennsieve-prod-discover-publish-use1"

NOT_SPECIFIED = 'not-specified'

def getDatasets(start, size):

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
            "objects.dataset",
            "pennsieve.version",
            "pennsieve.identifier",
            "pennsieve.uri"
        ]
    }

    return requests.post(urljoin(scicrunch_host, '_search?preference=abiknowledgetesting'), json=scicrunch_request, params=params, headers=headers)

def extract_bucket_name(original_name):
    return original_name.split('/')[2]


#Test object to check for any possible error
def testBiolucida(id, version, obj, biolucida_id, bucket):
    fileResponse = None
    global pennsieveCache


    localPath = obj['dataset']['path']

    try:

        biolucida_response = requests.get(f'{Config.BIOLUCIDA_ENDPOINT}/image/{biolucida_id}')
        if not biolucida_response.status_code == 200:
            return {
                'Path': localPath,
                'biolucida_id': biolucida_id,
                'Reason': 'Cannot get a valid request from Biolucida',
            }
            
        image_info = biolucida_response.json()

        if image_info['status'] == "permission denied":
            return {
                'Path': localPath,
                'biolucida_id': biolucida_id,
                'Reason': 'Biolucida permission denied',
            }
        #Check if file path is consistent between scicrunch and biolucida
        if not 'name' in image_info or not image_info['name'] in localPath:
            fileResponse = {
                'Path': localPath,
                'biolucida_id': biolucida_id,
                'Reason': 'Conflict between biolucida and scicrunch response',
            }
        else:
            #now check if the file path is consistent between Pennsieve and
            #the other two
            filePath = "files/" + localPath
            folderPath = filePath.rsplit("/", 1)[0]
            files = []
            if folderPath in pennsieveCache:
                files = pennsieveCache[folderPath]
            else:
                fileUrl = '{api}/datasets/{id}/versions/{version}/files/browse?path={folderPath}'.format( 
                    api=Config.PENNSIEVE_API_HOST, id=id, version=version, folderPath=folderPath)
                file_response = requests.get(fileUrl)
                files_info = file_response.json()
                    #print(files_info)
                if 'files' in files_info:
                    files = files_info['files']

            if len(files) > 0:
                pennsieveCache[folderPath] = files
                lPath = filePath.lower()
                foundFile = False
                for localFile in files:
                    if lPath == localFile['path'].lower():
                        foundFile = True
                        break
                    elif 'uri' in localFile:
                        uriFile = localFile['uri'].rsplit("/", 1)[0]
                        if uriFile:
                            uriFile = uriFile.lower()
                            if uriFile in filePath:
                                foundFile = True
                                break
                if not foundFile:
                    fileResponse = {
                        'Path': localPath,
                        'biolucida_id': biolucida_id,
                        'Reason': 'File path cannot be found on Pennsieve',
                    }
            else:
                fileResponse = {
                    'Path': localPath,
                    'biolucida_id': biolucida_id,
                    'Reason': 'Folder path cannot be found on Pennsieve',
                }
    except Exception as e:    
        fileResponse = {
            'Path': localPath,
            'biolucida_id': biolucida_id,
            'Reason': str(e)
        }

    return fileResponse

def test_biolucida_list(id, version, obj_list, bucket):
    objectErrors = []
    foundBiolucida = False
    global pennsieveCache
    pennsieveCache = {}
    datasetErrors = []
    biolucidaIDFound = False
    biolucidaInfoFound = False
    biolucidaFound = False

    biolucida_response = requests.get(f'{Config.BIOLUCIDA_ENDPOINT}/imagemap/search_dataset/discover/{id}')
    if biolucida_response.status_code == 200:
        dataset_info = biolucida_response.json()
        if 'status' in dataset_info and dataset_info['status'] == "success":
            biolucidaInfoFound = True

    for obj in obj_list:
        biolucida = obj.get('biolucida', NOT_SPECIFIED)
        if biolucida != NOT_SPECIFIED:
            biolucida_id = biolucida.get('identifier')
            if biolucida_id:
                biolucidaIDFound = True
                error = testBiolucida(id, version, obj, biolucida_id, bucket)
                if error:
                    objectErrors.append(error)

    if biolucidaIDFound or biolucidaInfoFound:
        biolucidaFound = True

    if biolucidaIDFound and not biolucidaInfoFound:
        datasetErrors.append({
            'Reason': 'One or more Biolucida ID found in SciCrunch but no image information is found on biolucida server.'
        })
    if not biolucidaIDFound and biolucidaInfoFound:
        datasetErrors.append({
            'Reason': 'Image information found on Biolucida server but no image id is found on SciCrunch.'
        })

    numberOfErrors = len(objectErrors)
    fileReports = {
        'Total': numberOfErrors,
        'Objects': objectErrors
    }
    return {"FileReports": fileReports, "DatasetErrors": datasetErrors, "BiolucidaFound": biolucidaFound}
                
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
                if 'objects' in source:
                    obj_list = source['objects']
                    obj_reports = test_biolucida_list(id, version, obj_list, bucket)
                    report['ObjectErrors'] = obj_reports['FileReports']
                    report['Errors'].extend(obj_reports["DatasetErrors"])
                    report['Biolucida'] = obj_reports['BiolucidaFound']
            else:
                report['Errors'].append('Missing version')
    return report


class BiolucidaDatasetFilesTest(unittest.TestCase):

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def test_files_information(self):

        start = 0
        size = 20
        keepGoing = True
        totalSize = 0
        reportOutput = 'reports/biolucida_reports.json'
        reports = {'Tested': 0, 'Failed': 0, 'FailedIds':[], 'Datasets':[]}
        testSize = 2000
        totalBiolucida = 0


        while keepGoing :
            scicrunch_response = getDatasets(start, size)
            self.assertEqual(200, scicrunch_response.status_code)

            data = scicrunch_response.json()

            #No more result, stop
            if size > len(data['hits']['hits']):
                keepGoing = False

            #keepGoing= False

            start = start + size

            for dataset in data['hits']['hits']:
                report = test_datasets_information(dataset)
                if 'Biolucida' in report and report['Biolucida']:
                    totalBiolucida = totalBiolucida + 1
                print(f"Reports generated for {report['Id']}")
                if len(report['Errors']) > 0 or report['ObjectErrors']['Total'] > 0:
                    reports['FailedIds'].append(report['Id'])
                    reports['Datasets'].append(report)

            totalSize = totalSize + len(data['hits']['hits'])

            if totalSize >= testSize:
                keepGoing = False

        # Generate the report
        reports['Tested'] = totalSize
        reports['Tested Datasets with Biolucida'] = totalBiolucida
        print(f"Number of datasets tested: {reports['Tested']}")
        reports['Failed'] = len(reports['FailedIds'])
        print(f"Number of dataset with erros: {reports['Failed']}")
        if reports['Failed'] > 0:
            print(f"Failed Datasets: {reports['FailedIds']}")
            
        os.makedirs(os.path.dirname(reportOutput), exist_ok=True)
        with open(reportOutput, 'w') as outfile:
            json.dump(reports, outfile, indent=4)
    
        print(f"Full report has been generated at {reportOutput}")

        self.assertEqual(0, len(reports['FailedIds']))

if __name__ == '__main__':
    unittest.main()
