# RLearn
**RLearn** aims to allow Keras and scikit-learn models to be trained remotely on a server with as little configuration required as possible. RLearn takes advantage of the server's existing Keras configuration and [H204GPU](https://github.com/h2oai/h2o4gpu) to accelerate training on the remote server even when the local machine doesnt have the hardware to do so.
##### **NOTE**: **This package is meant for individual developers who either have an existing desktop with a GPU, or a GPU compute instance on some cloud and wishes to use it to accelerate their machine learning workflow. It could be used in a professional setting but there are no garuntees as to its correctness, security, or robustness so this is not recommended as it could fail at ANY time.**
#### Why not just remotely host a Jupyter notebook for training?
Most of the data pre and postprocessing doesn't need to be done on a GPU accelerated machine. Keeping that computation remotely allows us to free up resources for training or running other applications on the machine.
## Usage
#### **Normal Usage :**
```python
session = RLearnSession('localhost:8765')
#session.train(model, x, y, compileargs, fitargs)
trained = session.train(model, x_train, y_train, {
  'loss': 'categorical_crossentropy',
  'optimizer': 'Adadelta',
  'metrics': ['accuracy']
}, {
  'batch_size': 128,
  'epochs': 10
})
```
#### **Advanced Usage :**
The underlying methods used by `RLearnSession.train()` can be used to make management and reuse of datasets, models, and jobs more efficient for your application.
```python
# This is an example from how one can break down the train() method for
# Keras' MNIST CNN model.
session = RLearnSession('localhost:8765')
#session.addData(x, y, name)
session.addData(x_train, y_train, 'mnistdata')
#session.addModel(model, name)
session.addModel(model, 'mnistmodel')
#session.addJob(jobtype, modelname, dataname, compileargs, fitargs)
trained = session.addJob('keras', 'mnistmodel', 'mnistdata',
               {
                    'loss': 'categorical_crossentropy',
                    'optimizer': 'Adadelta',
                    'metrics': ['accuracy']
               },
               {
                    'batch_size': 128,
                    'epochs': 10
               })
```
