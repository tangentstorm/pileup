"""
hand-spun aiohttp client for couchdb
"""
from datetime import datetime
import aiohttp

class CouchDBClient:

    def __init__(self, user, pswd, db, host='localhost', port=5984):
        self.sess = aiohttp.ClientSession()
        self.url = f'http://{user}:{pswd}@{host}:{port}/{db}'

    async def find(self, selector=None, **kw):
        q = {'selector': selector or kw, 'sort': [{'ts': 'desc'}]}
        async with self.sess.post(f'{self.url}/_find', json=q) as r:
            return await r.json()

    async def add_scrap(self, text: str, pile: str = '@inbox'):
        when = datetime.now().isoformat()
        async with self.sess.post(f'{self.url}', json={'text': text, 'pile': pile, 'ts': when}) as r:
            return await r.json()

    async def put(self, path, **obj):
        async with self.sess.put(f'{self.url}/{path}', json=obj) as r:
            return await r.json()
