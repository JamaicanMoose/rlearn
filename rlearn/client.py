import asyncio
import websockets
import base64 as b64
import dill
from keras.models import Sequential
import numpy as np
import rlearn.serialization as rls
import hashlib

def digest(bytes):
    return hashlib.md5(bytes).hexdigest()

class RLearnSession:
    def __init__(self, serverUrl):
        self.server = 'ws://' + serverUrl
        self.eventloop = asyncio.get_event_loop()
        self.session = None
        self.connect()

    def __del__(self):
        self.close()

    #def train(self, type, model, mname, ):

    def connect(self):
        async def cnct():
            self.session = await websockets.connect(self.server, max_size=None)
        self.eventloop.run_until_complete(cnct())

    def close(self):
        async def cls():
            await self.session.close()
        self.eventloop.run_until_complete(cls())

    def addData(self, x, y, name):
        async def f():
            await self.send_data(x, y, name)
        self.eventloop.run_until_complete(f())
        
    def addModel(self, model, name = ''):
        async def f():
            await self.send_model(model, name)
        self.eventloop.run_until_complete(f())

    def addJob(self, type, model, data, compileargs = {}, fitargs = {}):
        async def f():
            res = await self.send_job(type, model, data, compileargs, fitargs)
            return rls.deserialize(res)
        return self.eventloop.run_until_complete(f())

    def listData(self):
        async def f():
            await self.list_data()
        self.eventloop.run_until_complete(f())

    async def list_data(self):
        await self.session.send(dill.dumps({'type': 'listdata'}))
        dlist = dill.loads(await self.session.recv())
        print(dlist)
        return dlist['list']

    async def list_models(self):
        await self.session.send(dill.dumps({'type': 'listmodels'}))
        mlist = dill.loads(await self.session.recv())
        print(mlist)
        return mlist['list']

    async def send_job(self, type, model, data, compileargs, fitargs):
        print('sending job')
        await self.session.send(dill.dumps({
            'type': 'job',
            'jobinfo': {
                'type': type,
                'data': data,
                'model': model,
                'compileargs': compileargs,
                'fitargs': fitargs
            }
        }))
        res = dill.loads(await self.session.recv())
        print(res['status'])
        if res['status'] == 'SUCCESS':
            return res['trained']
        else:
            raise Exception('Training Failed')

    async def send_model(self, model, name):
        onserv = await self.list_models()
        mstr = rls.serialize(model).encode('utf-8')
        hsh = digest(mstr)
        nm = name if name != '' else hsh
        modeldata = {
            'name': nm,
            'hash': hsh
        }
        samehsh = list(filter(lambda a: a[1] == hsh, onserv))
        if samehsh:
            samename = list(filter(lambda a: a[0] == nm, samehsh))
            if samename:
                return
            else:
                modeldata['copy'] = False
                modeldata['copyname'] = samehsh[0][0]
        else:
            modeldata['copy'] = False
            modeldata['modelstr'] = mstr
        await self.session.send(dill.dumps({
            'type': 'model',
            'modeldata': modeldata
        }))
        resp = await self.session.recv()
        print(dill.loads(resp))

    async def send_data(self, x, y, name):
        onserv = await self.list_data()
        dstr = dill.dumps({'x': rls.serialize(x), 'y': rls.serialize(y)})
        hsh = digest(dstr)
        data = {'name': name, 'hash': hsh}
        samehsh = list(filter(lambda a: a[1] == hsh, onserv))
        if samehsh:
            samename = list(filter(lambda a: a[0] == name, samehsh))
            if samename:
                return
            else:
                data['copy'] = True
                data['copyname'] = samehsh[0][0]
        else:
            data['copy'] = False
            data['datastr'] = dstr

        await self.session.send(dill.dumps({
            'type': 'data',
            'data': data
        }))

        resp = await self.session.recv()
        print(dill.loads(resp))

