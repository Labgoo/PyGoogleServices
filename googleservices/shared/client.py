import json
from googleapiclient import http, model
from googleapiclient.errors import HttpError
from googleservices.shared.errors import GoogleCloudError

__author__ = 'krakover'


class GoogleCloudModel(model.JsonModel):
    """Adds optional global parameters to all requests."""

    def __init__(self, trace=None, **kwargs):
        super(GoogleCloudModel, self).__init__(**kwargs)
        self.trace = trace

    def request(self, headers, path_params, query_params, body_value):
        """Updates outgoing request."""
        if 'trace' not in query_params and self.trace:
            query_params['trace'] = self.trace

        return super(GoogleCloudModel, self).request(headers, path_params, query_params, body_value)


# pylint: disable=E1002
class GoogleCloudHttp(http.HttpRequest):
    """Converts errors into CloudStorage errors."""

    def __init__(self, http_model, *args, **kwargs):
        super(GoogleCloudHttp, self).__init__(*args, **kwargs)
        self._model = http_model

    @staticmethod
    def factory(storage_model):
        """Returns a function that creates a CloudStorageHttp with the given model."""
        def _create_cloudstorage_http_request(*args, **kwargs):
            captured_model = storage_model
            return GoogleCloudHttp(captured_model, *args, **kwargs)

        return _create_cloudstorage_http_request

    def execute(self, **kwargs):
        try:
            return super(GoogleCloudHttp, self).execute(**kwargs)
        except HttpError, e:
            self._model._log_response(e.resp, e.content)

            if e.resp.get('content-type', '').startswith('application/json'):
                result = json.loads(e.content)
                error = result.get('error', {}).get('errors', [{}])[0]
                raise GoogleCloudError.create(error, result, [])
            else:
                raise GoogleCloudError(
                    ('Could not connect with Google Cloud Storage server.\n'
                     'Http response status: %s\n'
                     'Http response content:\n%s') % (e.resp.get('status', '(unexpected)'), e.content))


