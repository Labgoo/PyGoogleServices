import logging
import random
import urllib
from urlparse import urlparse, parse_qs, urlunparse
from StringIO import StringIO
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import time
from googleservices.googledrive.errors import GoogleDriveError
from googleservices.shared.base_client import GoogleCloudClient
from googleservices.shared.client import GoogleCloudModel, GoogleCloudHttp

__author__ = 'barakcoh'


class GoogleDriveService(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        super(GoogleDriveService, self).__init__(use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)

        self.retry_count = 0
        self.max_retry_count = 5
        self.trace = trace

    def files(self):
        """Returns the objects Resource."""
        return self.api_client.files()

    def create(self, content_string, title, parent_id=None, mimetype='text/csv', description='', convert=False):
        io = StringIO()
        io.write(content_string)

        media_body = MediaIoBaseUpload(io, mimetype=mimetype, resumable=True)
        body = {
            'title': title,
            'mimeType': mimetype,
            'description': description
        }

        if parent_id is not None:
            body['parents'] = [{'id': parent_id}]

        try:
            return self.files().insert(body=body, media_body=media_body, convert=convert).execute()

        except HttpError, error:
            logging.exception(error.content)
            raise error

    def delete(self, file_id):
        try:
            return self.files().delete(fileId=file_id).execute()

        except HttpError, error:
            logging.exception(error.content)
            raise error

    def get(self, file_id, fmt='csv'):
        metadata = self.files().get(fileId=file_id).execute()

        url = metadata['exportLinks'].values()[0]
        export_url = self._replace_query_param(url, 'exportFormat', fmt)

        try:
            return self.files().request(export_url, 'GET')  # returns resp, content

        except HttpError, error:
            logging.exception(error.content)
            raise error

    # pylint: disable=R0914
    def update(self, file_id, content_string, title=None, mimetype='text/csv', description=None, new_revision=True,
               convert=True, parent_id=None):
        io = StringIO()
        io.write(content_string)

        body = {
            'mimeType': mimetype
        }

        if title is not None:
            body['title'] = title

        if description is not None:
            body['description'] = description

        if parent_id is not None:
            body['parents'] = [{'id': parent_id}]

        try:
            media_body = MediaIoBaseUpload(io, mimetype, resumable=True)
            io.close()

            return self.files().update(
                fileId=file_id, body=body, newRevision=new_revision, convert=convert,
                media_body=media_body
            ).execute()

        except HttpError, error:
            exception = None
            error_code = int(error.resp['status'])

            if self.retry_count < self.max_retry_count:
                if 500 <= error_code < 505:
                    sleep_secs_amount = float(2 ** self.retry_count) + (random.randint(0, 1000) / 1000.0)
                    self.retry_count += 1

                    logging.warning(
                        'Backing off from uploading to G-Drive. retry count: %s. Waiting for %s seconds',
                        self.retry_count, sleep_secs_amount
                    )

                    time.sleep(sleep_secs_amount)
                    self.update(file_id, content_string, mimetype, title, description, new_revision, convert, parent_id)

            else:
                if self.retry_count == self.max_retry_count:
                    exception = GoogleDriveError('Backed off as much as allowed. giving up.')

            # pylint: disable=E0702
            if exception is not None:
                failed_upload_format = 'Failed in uploading a file to G-Drive. Error code: %s. File ID: %s'
                logging.error(failed_upload_format, error_code, file_id)
                raise exception

        except Exception, exception:
            logging.exception('Exception of an unexpected type thrown. type: %s', type(exception))
            logging.exception(exception)
            raise exception

    def _replace_query_param(self, url, param, new_value):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params[param] = new_value
        return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params,
                           urllib.urlencode(query_params, True), parsed_url.fragment))

    @property
    def api_client(self):
        _http = self.get_http_for_request()

        drive_model = GoogleCloudModel(trace=self.trace)
        drive_http = GoogleCloudHttp.factory(drive_model)

        return build('drive', 'v2', http=_http, model=drive_model, requestBuilder=drive_http)
