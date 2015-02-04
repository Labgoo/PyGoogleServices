import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import httplib2
from googleservices.client import GoogleCloudHttp, GoogleCloudModel
from googleservices.utils import get_google_credentials

__author__ = 'krakover'


class GoogleCloudStorageClient(object):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleCloudStorageClient, self).__init__()
        self.trace = trace
        self.use_jwt_credentials_auth = use_jwt_credentials_auth
        self.jwt_account_name = jwt_account_name
        self.jwt_key_func = jwt_key_func
        self.oauth_credentails_file = oauth_credentails_file

        self._credentials = None

    def read_file(self, bucket_name, file_name):
        return self.objects().get_media(bucket=bucket_name, object=file_name).execute()

    def read_file_metadata(self, bucket_name, file_name):
        return self.objects().get(bucket=bucket_name, object=file_name).execute()

    def write_file(self, bucket_name, file_name, content, content_type):
        media = MediaIoBaseUpload(io.BytesIO(content), content_type)
        response = self.objects().insert(bucket=bucket_name, name=file_name, media_body=media).execute()

        return response

    def bucketAccessControls(self):
        """Returns the bucketAccessControls Resource."""
        return self.api_client.bucketAccessControls()

    def buckets(self):
        """Returns the buckets Resource."""
        return self.api_client.buckets()

    def channels(self):
        """Returns the channels Resource."""
        return self.api_client.channels()

    def defaultObjectAccessControls(self):
        """Returns the defaultObjectAccessControls Resource."""
        return self.api_client.defaultObjectAccessControls()

    def objects(self):
        """Returns the objects Resource."""
        return self.api_client.objects()

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
