import os


class Config(object):
    PENNSIEVE_API_HOST = os.environ['PENNSIEVE_API_HOST']
    PENNSIEVE_API_SECRET = os.environ['PENNSIEVE_API_SECRET']
    PENNSIEVE_API_TOKEN = os.environ['PENNSIEVE_API_TOKEN']
    SCICRUNCH_API_HOST = os.environ['SCICRUNCH_API_HOST']
    SCICRUNCH_API_KEY = os.environ['SCICRUNCH_API_KEY']
