from googleapiclient.discovery import build
from googleservices.shared.base_client import GoogleCloudClient
from googleservices.shared.client import GoogleCloudHttp, GoogleCloudModel

__author__ = 'krakover'


class GoogleTaskQueueClient(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleTaskQueueClient, self).__init__(use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)
        self.trace = trace

    def get_queue_stats(self, project_id, queue_name):
        qdata = self.taskqueues().get(project='s~' + project_id, taskqueue=queue_name, getStats=True).execute()

        return qdata[u'stats']

    def taskqueues(self):
        """Returns the taskqueues Resource."""
        return self.api_client.taskqueues()

    @property
    def api_client(self):
        _http = self.get_http_for_request()
        taskqueue_model = GoogleCloudModel(trace=self.trace)
        taskqueue_http = GoogleCloudHttp.factory(taskqueue_model)

        return build('taskqueue', 'v1beta2', http=_http, model=taskqueue_model, requestBuilder=taskqueue_http)
