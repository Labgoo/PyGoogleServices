import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleservices.shared.base_client import GoogleCloudClient
from googleservices.shared.client import GoogleCloudHttp, GoogleCloudModel

__author__ = 'krakover'


class GoogleCloudStorageClient(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleCloudStorageClient, self).__init__(use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)
        self.trace = trace

    def read_file(self, bucket_name, file_name):
        return self.objects().get_media(bucket=bucket_name, object=file_name).execute()

    def read_file_metadata(self, bucket_name, file_name):
        return self.objects().get(bucket=bucket_name, object=file_name).execute()

    def write_file(self, bucket_name, file_name, content, content_type):
        media = MediaIoBaseUpload(io.BytesIO(content), content_type)
        response = self.objects().insert(bucket=bucket_name, name=file_name, media_body=media).execute()

        return response

    def delete_file(self, bucket_name, file_name):
        return self.objects().delete(bucket=bucket_name, name=file_name)

    def list_files(self, bucket_name, prefix=None):
        return self.objects().list(bucket=bucket_name, projection=None, versions=None, prefix=prefix, maxResults=None, pageToken=None, delimiter=None)

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
    def api_client(self):
        _http = self.get_http_for_request()
        cloudstorage_model = GoogleCloudModel(trace=self.trace)
        cloudstorage_http = GoogleCloudHttp.factory(cloudstorage_model)

        return build("storage", "v1", http=_http, model=cloudstorage_model, requestBuilder=cloudstorage_http)
