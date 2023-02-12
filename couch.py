"""
hand-spun aiohttp client for couchdb
"""
import aiohttp

class CouchDBClient:

    def __init__(self, user, pswd, db, host='localhost', port=5984):
        self.sess = aiohttp.ClientSession()
        self.url = f'http://{user}:{pswd}@{host}:{port}/{db}'

    async def find(self, selector, **kw):
        async with self.sess.post(f'{self.url}/_find', json={'selector': selector}) as r:
            return await r.json()
