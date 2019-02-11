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
import signal

# ML Imports
import keras
import numpy as np

#db = shelve.open('shelf', writeback=True)

db = {}

def keyboardInterruptHandler(sg, fr):
    asyncio.get_event_loop().stop()
    #db.close()
    exit(0)


signal.signal(signal.SIGINT, keyboardInterruptHandler)

'''
{
    kmodels: {
        name: {hash, modelstr}
    }
    dataentries: {
        name: {hash, saveddata}
    }
    jobs: {
        'modelhash'+'datahash'+'argshash': {mname, dname, compileargs, fitargs, trainedmodel}
    }
}
'''

if 'kmodels' not in db:
    db['kmodels'] = {}
if 'dataentries' not in db:
    db['dataentries'] = {}
if 'jobs' not in db:
    db['jobs'] = {}

def digest(bytes):
    return hashlib.md5(bytes).hexdigest()

async def handle(websocket, path):
    async for message in websocket:
        obj = dill.loads(message)
        if obj['type'] == 'ping':
            print('socket<ping>');
            await websocket.send('pong')
        elif obj['type'] == 'model':
            print('socket<model>')
            await handle_model(websocket, obj['modeldata'])
        elif obj['type'] == 'data':
            print('socket<data>')
            await handle_data(websocket, obj['data'])
        elif obj['type'] == 'listdata':
            print('socket<listdata>')
            await handle_listdata(websocket)
        elif obj['type'] == 'listmodels':
            print('socket<listmodels>')
            await handle_listmodels(websocket)
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
        #Get stored pairs
        mdobj = db['kmodels'][jobinfo['model']]
        dobj = db['dataentries'][jobinfo['data']]
        #Create hash of args
        argshsh = digest(dill.dumps(jobinfo['compileargs'])) + \
                  digest(dill.dumps(jobinfo['fitargs']))
        jobhash = mdobj['hash'] + dobj['hash'] + argshsh
        #If weve already done this job, just return the result
        if jobhash in db['jobs'] and db['jobs'][jobhash]['trainedmodel']:
            await websocket.send(dill.dumps({
                'status': 'SUCCESS',
                'trained': db['jobs'][jobhash]['trainedmodel']
            }))
        else:
            #Add job entry to db
            db['jobs'][jobhash] = {
                'mname': jobinfo['model'],
                'dname': jobinfo['data'],
                'compileargs': jobinfo['compileargs'],
                'fitargs': jobinfo['fitargs'],
                'trainedmodel': None
            }
            #Train model
            model = rls.deserialize(str(mdobj['modelstr']))
            x = rls.deserialize(dobj['dataobj']['x'])
            y = rls.deserialize(dobj['dataobj']['y'])
            model.compile(**(jobinfo['compileargs']))
            model.fit(x=x, y=y, **(jobinfo['fitargs']))
            mdstr = rls.serialize(model)
            #Add trained model to job entry
            db['jobs'][jobhash]['trainedmodel'] = mdstr
            #db.sync()
            #Send trained model
            await websocket.send(dill.dumps({
                'status': 'SUCCESS',
                'trained': mdstr
            }))

async def handle_listmodels(websocket):
    await websocket.send(dill.dumps({
        'status': 'SUCCESS',
        'list': [(k, db['kmodels'][k]['hash']) for k in db['kmodels'].keys()]
    }))

async def handle_listdata(websocket):
    await websocket.send(dill.dumps({
        'status': 'SUCCESS',
        'list': [(k, db['dataentries'][k]['hash']) for k in db['dataentries'].keys()]
    }))

async def handle_model(websocket, modeldata):
    '''
        {
            'name': namestr
            'hash': hash of modelstr
            'modelstr': string saved model
        }
    '''
    if modeldata['copy']:
        print(modeldata['name'], ' in DB')
        db['kmodels'][modeldata['name']] = db['dataentries'][modeldata['copyname']]
    else:
        db['kmodels'][modeldata['name']] = {
            'hash': modeldata['hash'],
            'modelstr': modeldata['modelstr']
        }
    #db.sync()
    await websocket.send(dill.dumps({
        'status': 'SUCCESS',
        'hash': modeldata['hash']
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
    if data['copy']:
        print(data['name'], ' in DB')
        db['dataentries'][data['name']] = db['dataentries'][data['copyname']]
    else:
        db['dataentries'][data['name']] = {
            'hash': data['hash'],
            'dataobj': dataobj
        }
    #db.sync()
    await websocket.send(dill.dumps({
        'status': 'SUCCESS',
        'hash': data['hash']
    }))

asyncio.get_event_loop().run_until_complete(
    websockets.serve(handle, 'localhost', 8765, max_size=None))
asyncio.get_event_loop().run_forever()
