from googleapiclient.discovery import build
from shared.base_client import GoogleCloudClient
from shared.client import GoogleCloudHttp, GoogleCloudModel

__author__ = 'krakover'


class GoogleDataStoreClient(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleDataStoreClient, self).__init__( use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)
        self.trace = trace

    def datasets(self):
        """Returns the objects Resource."""
        return self.api_client.datasets()

    def get_entity_by_id(self, project_id, entity_name, entity_id):
        return self.datasets.lookup(datasetId=project_id, body={
            'keys': [{'path': [{'kind': entity_name, 'name': entity_id}]}],
        }).execute()

    @property
    def api_client(self):
        _http = self.get_http_for_request()
        cloudstorage_model = GoogleCloudModel(trace=self.trace)
        cloudstorage_http = GoogleCloudHttp.factory(cloudstorage_model)

        return build("storage", "v1", http=_http, model=cloudstorage_model, requestBuilder=cloudstorage_http)