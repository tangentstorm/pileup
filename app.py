"""
pileup web backend. mostly middleware to couchdb.
"""
from quart import Quart
import config

app = Quart(__name__)

@app.before_serving
async def startup():
    app.client = await config.get_client()
    # making any request seems to "warm up" the underlying aiohttp client.
    # otherwise there's a slight delay on the first request
    await app.client.sess.get(app.client.url)

@app.route('/')
async def index():
    return await app.send_static_file('index.html')


@app.route('/inbox')
async def inbox():
    return (await app.client.find({'pile': '@inbox'}))['docs']


if __name__ == '__main__':
    app.run()
