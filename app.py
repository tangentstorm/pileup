"""
pileup web backend. mostly middleware to couchdb.
"""
from quart import Quart, request
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


@app.route('/p/', defaults={'pile': '@inbox'})
@app.route('/p/<pile>', methods=['GET', 'POST'])
async def inbox(pile):
    match request.method:
        case 'GET':
            return (await app.client.find({'pile': pile}))['docs']
        case 'POST':
            text = (await request.json).get('text')
            return await app.client.add_scrap(text, pile)

@app.route('/s/<sid>', methods=['GET', 'PUT'])
async def scrap(sid):
    docs = (await app.client.find({'_id': sid}))['docs']
    res = docs[0] if docs else {}
    print(res)
    if res and request.method == 'PUT':
        # only thing you can edit is the pile (for now?)
        req = await request.json
        if pile := req.get('pile'):
            res['pile'] = pile
            res = await app.client.put(sid, **res)
    return res


if __name__ == '__main__':
    app.run()
