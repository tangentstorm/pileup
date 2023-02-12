"""
config file for pileup server.
rename this to config.py and fill in your credentials.
"""
from couch import CouchDBClient

async def get_client():
    return CouchDBClient('couch-userid', 'couch-password', 'couch-database-name')
