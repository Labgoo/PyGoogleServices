import logging
import os
import datetime
import httplib2
from oauth2client.file import Storage
from shared.errors import GoogleCloudAuthorizationConfigurationError, GoogleCloudComputeFailedToGetMetaDataError

__author__ = 'krakover'


def get_google_credentials(use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None):
    if use_jwt_credentials_auth:  # Local debugging using pem file
        scope = 'https://www.googleapis.com/auth/devstorage.read_write'
        from oauth2client.client import SignedJwtAssertionCredentials
        logging.debug("Using Standard jwt authentication")
        return SignedJwtAssertionCredentials(jwt_account_name, jwt_key_func(), scope=scope)
    elif is_in_appengine():  # App engine
        scope = 'https://www.googleapis.com/auth/devstorage.read_write'
        from oauth2client.appengine import AppAssertionCredentials
        logging.debug("Using Standard appengine authentication")
        return AppAssertionCredentials(scope=scope)
    elif oauth_credentails_file:  # Local oauth token
        storage = Storage(oauth_credentails_file)
        logging.debug("Using Standard OAuth authentication")
        credentials = storage.get()
        if not credentials:
            raise GoogleCloudAuthorizationConfigurationError('No credential file present')
        return credentials
    elif is_in_gce_machine():  # GCE authorization
        from oauth2client import gce
        logging.debug("Using GCE authentication")
        return gce.AppAssertionCredentials('')
    raise GoogleCloudAuthorizationConfigurationError('No Credentials provided')


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


def get_gce_zone(http):
    return get_gce_metadata(http, 'zone')


def get_gce_unique_id(http):
    return get_gce_metadata(http, 'id')


def get_gce_metadata(http, field):
    try:
        response, field_value = http.request(
            'http://metadata.google.internal/computeMetadata/v1beta1/instance/%s' % field)
    except httplib2.ServerNotFoundError, e:
        raise GoogleCloudComputeFailedToGetMetaDataError('Not on gce machine', e.message, None)

    if int(response['status']) != 200:
        logging.error('Error getting machine id: %s', response)
        raise GoogleCloudComputeFailedToGetMetaDataError('Error getting %s' % field, None, None)  # TODO parse error

    return field_value


def get_timestamp_RFC3375():
    # TODO add the correct microseconds, with 2 characters
    now = datetime.datetime.now()
    now = now.replace(microsecond=0)
    timestamp = now.isoformat('T') + '.00Z'  # Create RFC 3375 date format
    return timestamp
