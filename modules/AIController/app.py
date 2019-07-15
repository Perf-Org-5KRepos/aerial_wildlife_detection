'''
    Main Bottle and routings for the AIController instance.

    2019 Benjamin Kellenberger
'''

from bottle import post, request, response, abort
from modules.AIController.backend.middleware import AIMiddleware


class AIController:

    def __init__(self, config, app):
        self.config = config
        self.app = app

        self.middleware = AIMiddleware(config)

        self.login_check = None

        self._init_params()
        self._initBottle()


    def _init_params(self):
        self.maxNumWorkers_train = self.config.getProperty(self, 'maxNumWorkers_train', type=int, fallback=-1)
        self.maxNumWorkers_inference = self.config.getProperty(self, 'maxNumWorkers_inference', type=int, fallback=-1)
        self.maxNumImages_inference = self.config.getProperty(self, 'maxNumImages_inference', type=int)


    def loginCheck(self, needBeAdmin=False):
        return True if self.login_check is None else self.login_check(needBeAdmin)


    def addLoginCheckFun(self, loginCheckFun):
        self.login_check = loginCheckFun


    def _initBottle(self):
        
        @self.app.post('/startTraining')
        def start_training():
            '''
                Manually requests the AIController to train the model.
                This still only works if there is no training process ongoing.
                Otherwise the request is aborted.
            '''
            if self.loginCheck(True):
                try:
                    status = self.middleware.start_training(minTimestamp='lastState', maxNumWorkers=self.maxNumWorkers_train)
                except Exception as e:
                    status = str(e)
                return { 'status' : status }

            else:
                abort(401, 'unauthorized')

        
        @self.app.post('/startInference')
        def start_inference():
            '''
                Manually requests the AIController to issue an inference job.
            '''
            if self.loginCheck(True):
                status = self.middleware.start_inference(forceUnlabeled=True, maxNumImages=self.maxNumImages_inference, maxNumWorkers=self.maxNumWorkers_inference)
                return { 'status' : status }
            
            else:
                abort(401, 'unauthorized')


        @self.app.post('/start')
        def start_model():
            '''
                Manually launches one of the model processes (train, inference, both, etc.),
                depending on the provided flags.
            '''
            #TODO: unverified
            if self.loginCheck(True):
                # parse parameters
                try:
                    params = request.json
                    doTrain = 'train' in params and params['train'] is True
                    doInference = 'inference' in params and params['inference'] is True
                
                    if doTrain:
                        if doInference:
                            status = self.middleware.start_train_and_inference(minTimestamp='lastState', maxNumWorkers_train=self.maxNumWorkers_train,
                                    forceUnlabeled_inference=True, maxNumImages_inference=self.maxNumImages_inference, maxNumWorkers_inference=self.maxNumWorkers_inference)
                        else:
                            status = self.middleware.start_training(minTimestamp='lastState', maxNumWorkers=self.maxNumWorkers_train)
                    else:
                        status = self.middleware.start_inference(forceUnlabeled=True, maxNumImages=self.maxNumImages_inference, maxNumWorkers=self.maxNumWorkers_inference)

                    return { 'status' : status }
                except:
                    abort(400, 'bad request')


        @self.app.get('/status')
        def check_status():
            '''
                Queries the middleware for any ongoing training worker processes
                and returns the stati of each in a dict.
            '''
            if self.loginCheck(False):
                try:
                    queryProject = 'project' in request.query
                    queryTasks = 'tasks' in request.query
                    queryWorkers = 'workers' in request.query
                    status = self.middleware.check_status(queryProject, queryTasks, queryWorkers)
                except Exception as e:
                    status = str(e)
                return { 'status' : status }

            else:
                abort(401, 'unauthorized')