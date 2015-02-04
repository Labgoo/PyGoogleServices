import logging
import os
import httplib2
from oauth2client import gce
from oauth2client.appengine import AppAssertionCredentials
from oauth2client.file import Storage
from googleservices.errors import GoogleCloudAuthorizationError


def get_google_credentials(use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None):
    if use_jwt_credentials_auth:  # Local debugging using pem file
        scope = 'https://www.googleapis.com/auth/devstorage.read_write'
        from oauth2client.client import SignedJwtAssertionCredentials
        credentials = SignedJwtAssertionCredentials(jwt_account_name, jwt_key_func(), scope=scope)
        logging.info("Using Standard jwt authentication")
        return credentials
    elif is_in_appengine():  # App engine
        scope = 'https://www.googleapis.com/auth/devstorage.read_write'
        credentials = AppAssertionCredentials(scope=scope)
        logging.info("Using Standard appengine authentication")
        return credentials
    elif oauth_credentails_file:  # Local oauth token
        storage = Storage(oauth_credentails_file)
        credentials = storage.get()
        if not credentials:
            raise GoogleCloudAuthorizationError('No credential file present')
        logging.info("Using Standard OAuth authentication")
        return credentials
    elif is_in_gce_machine():  # GCE authorization
        credentials = gce.AppAssertionCredentials('')
        logging.info("Using GCE authentication")
        return credentials
    raise GoogleCloudAuthorizationError('No Credentials provided')


def is_in_appengine():
    return 'SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'].startswith('Google App Engine/')


def is_in_gce_machine():
    try:
        metadata_uri = 'http://metadata.google.internal'
        _http = httplib2.Http()
        _http.request(metadata_uri, method='GET')
        return True
    except httplib2.ServerNotFoundError:
        return False


def get_gce_unique_id(self):
    resp, unique_machine_id = self.get_http_for_request().request(
        'http://metadata.google.internal/computeMetadata/v1beta1/instance/id')

    if int(resp['status']) != 200:
        logging.error("Error getting machine id: %s", resp)
        return None
    return unique_machine_id