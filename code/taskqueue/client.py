from googleapiclient.discovery import build
import httplib2
from googleservices.client import GoogleCloudHttp, GoogleCloudModel
from googleservices.utils import get_google_credentials

__author__ = 'krakover'


class GoogleTaskQueueClient(object):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleTaskQueueClient, self).__init__()
        self.trace = trace
        self.use_jwt_credentials_auth = use_jwt_credentials_auth
        self.jwt_account_name = jwt_account_name
        self.jwt_key_func = jwt_key_func
        self.oauth_credentails_file = oauth_credentails_file

        self._credentials = None

    def get_queue_stats(self, project_id, queue_name):
        qdata = self.taskqueues().get(project='s~' + project_id, taskqueue=queue_name, getStats=True).execute()

        return qdata[u'stats']

    def taskqueues(self):
        """Returns the taskqueues Resource."""
        return self.api_client.taskqueues()

    @property
    def credentials(self):
        if not self._credentials:
            self._credentials = get_google_credentials(self.use_jwt_credentials_auth, self.jwt_account_name, self.jwt_key_func, self.oauth_credentails_file)
        return self._credentials

    def get_http_for_request(self):
        _http = httplib2.Http()
        _http = self.credentials.authorize(_http)
        self.credentials.refresh(_http)

        return _http

    @property
    def api_client(self):
        _http = self.get_http_for_request()
        taskqueue_model = GoogleCloudModel(trace=self.trace)
        taskqueue_http = GoogleCloudHttp.factory(taskqueue_model)

        return build("storage", "v1", http=_http, model=taskqueue_model, requestBuilder=taskqueue_http)
