from googleapiclient.discovery import build
import httplib2
from googleservices.client import GoogleCloudHttp, GoogleCloudModel
from googleservices.utils import get_google_credentials

__author__ = 'krakover'


class GoogleDataStoreClient(object):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleDataStoreClient, self).__init__()
        self.trace = trace
        self.use_jwt_credentials_auth = use_jwt_credentials_auth
        self.jwt_account_name = jwt_account_name
        self.jwt_key_func = jwt_key_func
        self.oauth_credentails_file = oauth_credentails_file

        self._credentials = None

    def datasets(self):
        """Returns the objects Resource."""
        return self.api_client.datasets()

    def get_entity_by_id(self, project_id, entity_name, entity_id):
        return self.datasets.lookup(datasetId=project_id, body={
            'keys': [{'path': [{'kind': entity_name, 'name': entity_id}]}],
        }).execute()

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
        cloudstorage_model = GoogleCloudModel(trace=self.trace)
        cloudstorage_http = GoogleCloudHttp.factory(cloudstorage_model)

        return build("storage", "v1", http=_http, model=cloudstorage_model, requestBuilder=cloudstorage_http)