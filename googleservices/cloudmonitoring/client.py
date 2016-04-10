import json
import logging
import httplib2

from googleapiclient.discovery import build
from googleservices.cloudmonitoring.errors import CloudMonitoringError
from googleservices.shared.base_client import GoogleCloudClient
from googleservices.shared.client import GoogleCloudHttp, GoogleCloudModel
from googleservices.shared.utils import get_google_credentials, get_gce_unique_id, get_timestamp_RFC3375, get_gce_zone

__author__ = 'krakover'


class GoogleCloudMonitoringClient(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(GoogleCloudMonitoringClient, self).__init__(use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)
        self.trace = trace

    def write_timeseries_custon_instance_metric_double_value(self, project_id, metric_name, double_value):
        self.write_timeseries_custon_instance_metric_int_value_v3(project_id, metric_name, double_value)
        # Need to also write to v2, as long as v3 is not supporting autoscaling
        self.write_timeseries_custon_instance_metric_int_value_v2(project_id, metric_name, double_value)

    def write_timeseries_custon_instance_metric_int_value_v3(self, project_id, metric_name, int_value):
        # pylint: disable=C0330
        timestamp = get_timestamp_RFC3375()
        http = self.get_http_for_request()

        # Writing not supported by API - TODO REST call remove once api supports this
        unique_machine_id = get_gce_unique_id(http)

        machine_zone = get_gce_zone(http)
        machine_zone = machine_zone[machine_zone.rfind('/')+1:]

        timeseries_dict = {'timeSeries': [{
            'metric': {
                'type': 'custom.googleapis.com/custom/%s' % metric_name,
                'labels': {},
            },
            'resource': {
                'type': 'gce_instance',
                'labels': {
                    'instance_id': unique_machine_id,
                    'zone': machine_zone
                }
            },
            'metricKind': 'GAUGE',
            'valueType': 'double',
            'points': [{
                'interval': {
                    'endTime': timestamp,
                    'startTime': timestamp,
                },
                'value': {
                    'doubleValue': int_value,
                },
            }]}],
        }

        resp, _ = http.request(
            uri='https://monitoring.googleapis.com/v3/projects/%s/timeSeries' % project_id,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(timeseries_dict))

        if int(resp['status']) != 200:
            logging.error('Error reporting to cloud monitoring: %s from instance %s', resp, unique_machine_id)
            raise CloudMonitoringError('received error %s while attempting to write time series data' % resp['status'])

    def write_timeseries_custon_instance_metric_int_value_v2(self, project_id, metric_name, int_value):
        # pylint: disable=C0330
        timestamp = get_timestamp_RFC3375()
        http = self.get_http_for_request()

        # Writing not supported by API - TODO REST call remove once api supports this
        unique_machine_id = get_gce_unique_id(http)

        timeseries_dict = {
            'kind': 'cloudmonitoring#writeTimeseriesRequest',
            'commonLabels': {
                'compute.googleapis.com/resource_type': 'instance',
                'compute.googleapis.com/resource_id': unique_machine_id
            },
            'timeseries': [{
                'timeseriesDesc': {
                    'metric': 'custom.cloudmonitoring.googleapis.com/custom/%s' % metric_name,
                    'labels': {}
                },
                'point': {
                    'start': timestamp,
                    'end': timestamp,
                    'doubleValue': int_value
                }
            }]
        }

        resp, _ = http.request(
            uri='https://www.googleapis.com/cloudmonitoring/v2beta2/projects/%s/timeseries:write' % project_id,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(timeseries_dict))

        if int(resp['status']) != 200:
            logging.error('Error reporting to cloud monitoring: %s from instance %s', resp, unique_machine_id)
            raise CloudMonitoringError('received error %s while attempting to write time series data' % resp['status'])

    @property
    def credentials(self):
        if not self._credentials:
            self._credentials = get_google_credentials(self.use_jwt_credentials_auth, self.jwt_account_name,
                                                       self.jwt_key_func, self.oauth_credentails_file)
        return self._credentials

    def get_http_for_request(self):
        _http = httplib2.Http()
        _http = self.credentials.authorize(_http)
        self.credentials.refresh(_http)

        return _http

    @property
    def api_client(self):
        return self.api_client_v3


    @property
    def api_client_v2(self):
        _http = self.get_http_for_request()
        monitoring_model = GoogleCloudModel(trace=self.trace)
        monitoring_http = GoogleCloudHttp.factory(monitoring_model)

        return build("cloudmonitoring", "v2beta2", http=_http, model=monitoring_model, requestBuilder=monitoring_http)


    @property
    def api_client_v3(self):
        _http = self.get_http_for_request()
        monitoring_model = GoogleCloudModel(trace=self.trace)
        monitoring_http = GoogleCloudHttp.factory(monitoring_model)

        return build("cloudmonitoring", "v3", http=_http, model=monitoring_model, requestBuilder=monitoring_http)
