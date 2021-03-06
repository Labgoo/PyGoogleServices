import json
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleservices.shared.base_client import GoogleCloudClient

from googleservices.shared.client import GoogleCloudModel, GoogleCloudHttp

from .errors import BigQueryError, BigQueryDuplicateError, \
                    BigQueryStreamingMaximumRowSizeExceededError


__author__ = 'ekampf'


# pylint: disable=E1002
class BigQueryHttp(GoogleCloudHttp):
    def execute(self, **kwargs):
        try:
            return super(BigQueryHttp, self).execute(**kwargs)
        except HttpError, e:
            self._model._log_response(e.resp, e.content)

            if e.resp.get('content-type', '').startswith('application/json'):
                result = json.loads(e.content)
                error = result.get('error', {}).get('errors', [{}])[0]
                raise BigQueryError.create(error, result, [])
            else:
                raise BigQueryError(
                    ('Could not connect with Google Cloud Storage server.\n'
                     'Http response status: %s\n'
                     'Http response content:\n%s') % (e.resp.get('status', '(unexpected)'), e.content))


# pylint: disable=E1002
class BigQueryClient(GoogleCloudClient):
    def __init__(self, use_jwt_credentials_auth=False, jwt_account_name='', jwt_key_func=None, oauth_credentails_file=None, trace=None):
        """
        :param trace: A value to add to all outgoing requests
        :return:
        """
        super(BigQueryClient, self).__init__(use_jwt_credentials_auth, jwt_account_name, jwt_key_func, oauth_credentails_file)
        self.trace = trace

    ###### Wrapping BigQuery's API

    def datasets(self):
        return self.api_client.datasets()

    def jobs(self):
        return self.api_client.jobs()

    def projects(self):
        return self.api_client.projects()

    def tabledata(self):
        return self.api_client.tabledata()

    def tables(self):
        return self.api_client.tables()


    @property
    def api_client(self):
        bigquery_model = GoogleCloudModel(trace=self.trace)
        bigquery_http = GoogleCloudHttp.factory(bigquery_model)

        http = self.get_http_for_request()
        return build("bigquery", "v2", http=http, model=bigquery_model, requestBuilder=bigquery_http)

    ###### Utility methods

    # tables() methods
    def create_table(self, project_id, dataset_id, table_id, fields, ignore_existing=False,
                     description=None, friendly_name=None, expiration=None):
        logging.info('create table %s on project %s dataset %s', table_id, project_id, dataset_id)

        body = {
            'tableReference': {
                'tableId': table_id,
                'datasetId': dataset_id,
                'projectId': project_id
            },
            'schema': {
                'fields': fields
            }
        }

        if friendly_name is not None:
            body['friendlyName'] = friendly_name
        if description is not None:
            body['description'] = description
        if expiration is not None:
            body['expirationTime'] = expiration

        try:
            logging.info('Creating table \ndatasetId:%s \nprojectId: %s \ntable_ref:%s', dataset_id, project_id, body)

            response = self.tables().insert(projectId=project_id, datasetId=dataset_id, body=body).execute()

            logging.info('%s create table response %s', project_id, response)

            return response
        except BigQueryDuplicateError:
            if not ignore_existing:
                raise

    # tabledata()  methods

    # pylint:disable=R0914
    def insert_rows(self, project_id, dataset_id, table_id, insert_id_generator, rows, ignore_invalid_rows=False):
        """Streams data into BigQuery one record at a time without needing to run a load job.

        :param application_id: Project ID of the destination table. (required)
        :param dataset_id: Dataset ID of the destination table. (required)
        :param table_id: Table ID of the destination table. (required)
        :param insert_id_generator: lambda that gets a row and generates an insertId.
        :param rows: The rows to insert (array or single object)
        :param ignore_invalid_rows: If True performs 2 inserts passes. On first pass, if there's an error google return "invalid" on error rows but doesnt insert anything (rest of the rows marked as "stopped").
                                    So we filter out "invalid" rows and do a 2nd pass.
                                    Note that this does not ignore if there's a BigQueryStreamingMaximumRowSizeExceeded error.
        :return:
          A response object (https://developers.google.com/resources/api-libraries/documentation/bigquery/v2/python/latest/bigquery_v2.tabledata.html#insertAll).
          If ignore_invalid_rows is True and there were error return object is a dict containing the response object for the 2 insert passes performed: dict(response_pass1=..., response_pass2=...)
        """
        if isinstance(rows, dict):
            rows = [rows]

        if insert_id_generator is not None:
            rows_json = [{'json': r, 'insertId': insert_id_generator(r)} for r in rows]
        else:
            rows_json = [{'json': r} for r in rows]

        body = {"rows": rows_json}

        try:
            logging.info("Inserting %s rows to projectId=%s, datasetId=%s, tableId=%s", len(rows), project_id, dataset_id, table_id)

            response = self.api_client.tabledata().insertAll(projectId=project_id, datasetId=dataset_id, tableId=table_id, body=body).execute()

            if 'insertErrors' in response:
                insert_errors = response['insertErrors']
                insert_errors_json = json.dumps(insert_errors)
                if insert_errors_json.find('Maximum allowed row size exceeded') > -1:
                    raise BigQueryStreamingMaximumRowSizeExceededError()

                logging.error("Failed to insert rows:\n%s", insert_errors_json)
                if ignore_invalid_rows:
                    invalid_indices = [err['index'] for err in insert_errors
                                       if any([x['reason'] == 'invalid' for x in err['errors']])]

                    rows_json_pass2 = [event for idx, event in enumerate(rows_json) if idx not in invalid_indices]

                    body_pass2 = {"rows": rows_json_pass2}
                    response2 = self.api_client.tabledata().insertAll(
                        projectId=project_id, datasetId=dataset_id, tableId=table_id, body=body_pass2).execute()

                    return dict(response_pass1=response, response_pass2=response2,
                                counts=dict(invalid_rows=len(invalid_indices), successfuly_added=len(rows_json_pass2)))

            logging.info("Successfully inserted %s rows", len(rows))
            return response
        except BigQueryError as ex:
            logging.exception(ex.message)
            raise

    # jobs() methods

    def create_insert_job(self, project_id, dataset_id, table_id, gcs_links, mode='WRITE_APPEND'):
        job_data = {
            'projectId': project_id,
            'configuration': {
                'load': {
                    'sourceFormat': 'NEWLINE_DELIMITED_JSON',
                    'writeDisposition': mode,
                    'sourceUris': ['gs://%s' % s for s in gcs_links],
                    'destinationTable': {
                        'projectId': project_id,
                        'datasetId': dataset_id,
                        'tableId': table_id
                    },
                }
            }
        }

        logging.info('about to insert job:%s', job_data)
        try:
            job = self.api_client.jobs().insert(projectId=project_id, body=job_data).execute()

            status = job['status']
            if 'errorResult' in status:
                raise BigQueryError.create(job['status']['errorResult'], None, job['status']['errors'], job['jobReference'])

            return job
        except BigQueryError as ex:
            logging.exception(ex)
            raise

    def monitor_insert_job(self, project_id, job_id):
        try:
            logging.info('about to monitor job: %s', job_id)
            job = self.api_client.jobs().get(projectId=project_id, jobId=job_id).execute()

            state = job['status']['state']
            if state == 'DONE':
                logging.info("Job %s is done loading!", job_id)
                if 'errorResult' in job['status']:
                    raise BigQueryError.create(job['status']['errorResult'], None, job['status']['errors'],
                                               {'projectId': project_id, 'jobId': job_id})
                return job
            return None

        except BigQueryError as ex:
            logging.exception(ex)
            raise

    def get_query_results(self, project_id, job_id, timeoutMs=None, pageToken=None, maxResults=None, startIndex=None):
        """Retrieves the results of a query job.
        :param project_id: Project ID of the query job.
        :param job_id: Job ID of the query job.
        :param timeoutMs: integer, How long to wait for the query to complete, in milliseconds, before returning. Default is to return immediately. If the timeout passes before the job completes, the request will fail with a TIMEOUT error.
        :param pageToken: string, Page token, returned by a previous call, to request the next page of results
        :param maxResults: integer, Maximum number of results to read
        :param startIndex: string, Zero-based index of the starting row
        :return:
        """

        try:
            return self.jobs().getQueryResults(projectId=project_id, jobId=job_id, timeoutMs=timeoutMs,
                                               pageToken=pageToken, maxResults=maxResults, startIndex=startIndex).execute()
        except BigQueryError as ex:
            logging.exception(ex)

    def run_query(self, project_id, query_string):
        """Retrieves the results of a query job.
        :param project_id: Project ID of the query job.
        :param query_string: SQL query of the query job.
        :return:
        """

        try:
            return self.jobs().insert(projectId=project_id,
                                      body={
                                          'configuration': {
                                              'query': {
                                                  'query': query_string,
                                              }
                                          }
                                      }).execute()
        except BigQueryError as ex:
            logging.exception(ex)
            raise

    def run_query_blocking(self, project_id, query_string):
        """Retrieves the results of a query job.
        :param project_id: Project ID of the query job.
        :param query_string: SQL query of the query job.
        :return:
        """

        try:
            insert_response = self.run_query(project_id, query_string)

            # Get query results. Results will be available for about 24 hours.
            current_row = 0
            response = self.get_query_results(
                project_id,
                insert_response['jobReference']['jobId'],
                startIndex=current_row)

            result = None
            while 'rows' in response and current_row < int(response['totalRows']):
                result = response
                current_row += len(response['rows'])

                response = self.get_query_results(
                    project_id,
                    response['jobReference']['jobId'],
                    startIndex=current_row)

            return result
        except BigQueryError as ex:
            logging.exception(ex)
            raise


