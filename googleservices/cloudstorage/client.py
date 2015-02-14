import base64
import io
import datetime
import md5
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import requests
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

    @staticmethod
    def create_signed_url(bucket_name, file_name, service_account_key_file, service_account_mail, expiration=None, ):
        keytext = open(service_account_key_file, 'rb').read()
        private_key = RSA.importKey(keytext)

        signer = CloudStorageURLSigner(private_key, service_account_mail, 'https://storage.googleapis.com', expiration=expiration)
        response = signer.get('/{0}/{1}'.format(bucket_name, file_name))
        return response.url

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


class CloudStorageURLSigner(object):
    """Contains methods for generating signed URLs for Google Cloud Storage."""

    def __init__(self, key, client_id_email, gcs_api_endpoint, expiration=None, session=None):
        """Creates a CloudStorageURLSigner that can be used to access signed URLs.

        Args:
          key: A PyCrypto private key.
          client_id_email: GCS service account email.
          gcs_api_endpoint: Base URL for GCS API.
          expiration: An instance of datetime.datetime containing the time when the
                      signed URL should expire.
          session: A requests.session.Session to use for issuing requests. If not
                   supplied, a new session is created.
        """
        self.key = key
        self.client_id_email = client_id_email
        self.gcs_api_endpoint = gcs_api_endpoint

        self.expiration = expiration or (datetime.datetime.now() + datetime.timedelta(days=1))
        self.expiration = int(datetime.time.mktime(self.expiration.timetuple()))

        self.session = session or requests.Session()

    def _base64_sign(self, plaintext):
        """Signs and returns a base64-encoded SHA256 digest."""
        shahash = SHA256.new(plaintext)
        signer = PKCS1_v1_5.new(self.key)
        signature_bytes = signer.sign(shahash)
        return base64.b64encode(signature_bytes)

    def _make_signature_string(self, verb, path, content_md5, content_type):
        """Creates the signature string for signing according to GCS docs."""
        signature_string = ('{verb}\n'
                            '{content_md5}\n'
                            '{content_type}\n'
                            '{expiration}\n'
                            '{resource}')
        return signature_string.format(verb=verb,
                                       content_md5=content_md5,
                                       content_type=content_type,
                                       expiration=self.expiration,
                                       resource=path)

    def _make_url(self, verb, path, content_type='', content_md5=''):
        """Forms and returns the full signed URL to access GCS."""
        base_url = '%s%s' % (self.gcs_api_endpoint, path)
        signature_string = self._make_signature_string(verb, path, content_md5, content_type)
        signature_signed = self._base64_sign(signature_string)
        query_params = {'GoogleAccessId': self.client_id_email,
                        'Expires': str(self.expiration),
                        'Signature': signature_signed}
        return base_url, query_params

    def get(self, path):
        """Performs a GET request.

        Args:
          path: The relative API path to access, e.g. '/bucket/object'.

        Returns:
          An instance of requests.Response containing the HTTP response.
        """
        base_url, query_params = self._make_url('GET', path)
        return self.session.get(base_url, params=query_params)

    def put(self, path, content_type, data):
        """Performs a PUT request.

        Args:
          path: The relative API path to access, e.g. '/bucket/object'.
          content_type: The content type to assign to the upload.
          data: The file data to upload to the new file.

        Returns:
          An instance of requests.Response containing the HTTP response.
        """
        md5_digest = base64.b64encode(md5.new(data).digest())
        base_url, query_params = self._make_url('PUT', path, content_type, md5_digest)
        headers = {}
        headers['Content-Type'] = content_type
        headers['Content-Length'] = str(len(data))
        headers['Content-MD5'] = md5_digest
        return self.session.put(base_url, params=query_params, headers=headers, data=data)

    def delete(self, path):
        """Performs a DELETE request.

        Args:
          path: The relative API path to access, e.g. '/bucket/object'.

        Returns:
          An instance of requests.Response containing the HTTP response.
        """
        base_url, query_params = self._make_url('DELETE', path)
        return self.session.delete(base_url, params=query_params)

