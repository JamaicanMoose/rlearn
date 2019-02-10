import numpy as np
import io
import base64 as b64
from keras.models import load_model, save_model, Model, Sequential
import re


def serialize(obj):
    buf = io.BytesIO()
    t = ''
    if isinstance(obj, Model):
        save_model(obj, buf)
        t = 'kermdl'
    elif isinstance(obj, np.ndarray):
        np.save(buf, obj)
        t = 'nparr'
    else:
        raise Exception('Object is not serializable with this method.')
    return ('##'+t+'##') + str(b64.b64encode(buf.getvalue()), 'ascii')


def deserialize(str):
    m = re.search('##([a-z]+)##(.*)', str)
    t = m.group(1)
    objstr = m.group(2)
    buf = io.BytesIO(b64.b64decode(objstr))
    decoded = None
    if t == 'kermdl':
        return load_model(buf)
    elif t == 'nparr':
        return np.load(buf)
    else:
        raise Exception('String is not deserializable with this method.')

