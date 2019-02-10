# Transport Imports
import asyncio
import websockets
import dill
import rlearn.serialization as rls

# Datastore Imports
import hashlib
import shelve

# CLI Imports
import argparse

# ML Imports
import keras
import numpy as np

db = shelve.open('./shelf.db', writeback=True)

'''
{
    kmodels: {
        name: (hash, savedmodel)
    }
    dataPairs: {
        name: (hash, saveddata)
    }
}
'''

if 'kmodels' not in db:
    db['kmodels'] = {}
if 'dataPairs' not in db:
    db['dataPairs'] = {}

async def handle(websocket, path):
    async for message in websocket:
        obj = dill.loads(message)
        if obj['type'] == 'ping':
            print('socket<ping>');
            await websocket.send('pong')
        elif obj['type'] == 'model':
            print('socket<model>')
        elif obj['type'] == 'data':
            print('socket<data>')
            await handle_data(websocket, obj['data'])
        elif obj['type'] == 'listdata':
            print('socket<listdata>')
            await handle_listdata(websocket)
        elif obj['type'] == 'job':
            print('socket<job>')
            await handle_job(websocket, obj['jobinfo'])

async def handle_job(websocket, jobinfo):
    '''
        {
            'type': keras | sklearn
            'data': dname
            'model': mname
        }
    '''
    if jobinfo['type'] == 'keras':
        model = rls.deserialize(db['kmodels'][jobinfo['model']])
        data = db['dataPairs'][jobinfo['data']]
        x = rls.deserialize(data['x'])
        y = rls.deserialize(data['y'])
        model.compile(**(jobinfo['compileargs']))
        model.fit(x=x, y=y, **(jobinfo['fitargs']))

async def handle_listdata(websocket):
    await websocket.send(dill.dumps({
        'status': 'SUCCESS',
        'list': list(db['dataPairs'].keys())
    }))

async def handle_data(websocket, data):
    '''
        {
            'name': namestr
            'hash': hash of datastr
            'datastr': pickled {x: xdatastr, y: ydatastr}
        }
    '''
    dataobj = dill.loads(data['datastr'])
    hash = hashlib.md5(data['datastr']).hexdigest()
    if hash == data['hash']:
        db['dataPairs'][data['name']] = (hash, dataobj)
        await websocket.send(dill.dumps({
            'status': 'SUCCESS',
            'hash': hash
        }))
    else:
        await websocket.send(dill.dumps({
            'status': 'FAILURE',
            'reason': 'CHECKSUM MISMATCH'
        }))

asyncio.get_event_loop().run_until_complete(
    websockets.serve(handle, 'localhost', 8765))
asyncio.get_event_loop().run_forever()
