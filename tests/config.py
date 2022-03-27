import os


class Config(object):
    PENNSIEVE_API_HOST = os.environ['PENNSIEVE_API_HOST']
    PENNSIEVE_API_SECRET = os.environ['PENNSIEVE_API_SECRET']
    PENNSIEVE_API_TOKEN = os.environ['PENNSIEVE_API_TOKEN']
    SCICRUNCH_API_HOST = os.environ['SCICRUNCH_API_HOST']
    SCICRUNCH_API_KEY = os.environ['SCICRUNCH_API_KEY']
    SCICRUNCH_APINATOMY_HOST = os.environ.get('SCICRUNCH_APINATOMY_HOST', 'https://scicrunch.org/api/1/sparc-scigraph/dynamic/demos/apinat')
    SCICRUNCH_SPARC_CYPHER = os.environ.get('SCICRUNCH_SPARC_CYPHER', 'http://sparc-data.scicrunch.io:9000/scigraph/cypher/execute')
    SPARC_PENNSIEVE_ORGANISATION_ID = 367
