"""
pileup web backend. mostly middleware to couchdb.
"""
from quart import Quart, request, Response
import json
import config

HEX = set("0123456789abcdef")

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
@app.route('/p/<key>', methods=['GET', 'PUT', 'POST'])
async def get_pile(key):
    if len(key) == 32 and all(ch in HEX for ch in key):
        pile = (await app.client.find(_id=key))
    else:
        if piles := (await app.client.find(type='pile', text=key))['docs']:
            # !! what if there's more than one pile with this name? (force unique?)
            pile = piles[0]
            key = pile['_id']
        elif key == '@inbox':
            pile = {'_id': key}
        else:
            print("no such pile:", key)
            return []
    match request.method:
        case 'GET':
            pile['items'] = (await app.client.find(pile=key))['docs']
            return pile
        case 'PUT':
            data = await request.json
            if 'items' in data:
                del data['items']
            return await app.client.put(key, **data)
        case 'POST':
            text = (await request.json).get('text')
            return await app.client.add_scrap(text, key)


def json_error(code, msg):
    return Response(json.dumps({"error": msg}), status=code, mimetype='application/json')


@app.route('/s/<sid>', methods=['GET', 'PUT'])
async def scrap(sid):
    docs = (await app.client.find({'_id': sid}))['docs']
    doc = docs[0] if docs else {}
    if doc and request.method == 'PUT':
        req = await request.json
        # !! should I whitelist fields here? for now, merge in anything
        if not "_rev" in req:
            return json_error(409, "no _rev provided")
        doc.update(req)
        doc = await app.client.put(sid, **doc)
    return doc


if __name__ == '__main__':
    app.run()
