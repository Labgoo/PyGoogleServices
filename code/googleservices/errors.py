import textwrap

__author__ = 'krakover'


class GoogleCloudError(Exception):
    # pylint: disable=R0911
    @staticmethod
    def parse_error(error, error_ls, job_ref):
        reason = error.get('error', None) or error.get('reason', None)
        if job_ref:
            message = 'Error processing %r: %s' % (job_ref, error.get('message'))
        else:
            message = error.get('message')
        new_errors = [err for err in error_ls if err != error]
        if new_errors:
            message += '\nFailure details:\n'
            message += '\n'.join(
                textwrap.fill(': '.join(filter(None, [err.get('location', None), err.get('message', '')])),
                              initial_indent=' - ', subsequent_indent='   ') for err in new_errors)
        return message, reason

    @staticmethod
    def create(error, server_error, error_ls, job_ref=None):
        """Returns a GoogleCloudStorageError for the JSON error that's embedded in the server error response.

        If error_ls contains any errors other than the given one, those are also included in the
        return message.

        :param error: The primary error to convert.
        :param server_error: The error returned by the server. (Only used in case error is malformed.)
        :param error_ls: Additional errors included in the error message.
        :param job_ref: A job reference if its an error associated with a job.
        :return:
          A GoogleCloudStorageError instance.
        """

        message, reason = GoogleCloudError.parse_error(error, error_ls, job_ref)

        if not reason or not message:
            return GoogleCloudInterfaceError('Error reported by server with missing error fields. ' 'Server returned: %s' % (str(server_error),))

        if reason == 'authError':
            return GoogleCloudAuthorizationError(message)

        if reason == 'notFound':
            return GoogleCloudNotFoundError(message, error, error_ls, job_ref=job_ref)
        if reason == 'backendError':
            return GoogleCloudAuthorizationError(message, error, error_ls, job_ref=job_ref)
        if reason == 'rateLimitExceeded':
            return GoogleCloudRateLimitExceededError(message, error, error_ls, job_ref=job_ref)
        if reason == 'dailyLimitExceeded':
            return GoogleCloudDailyLimitExceededError(message, error, error_ls, job_ref=job_ref)
        if reason == 'accessDenied':
            return GoogleCloudServiceError(message, error, error_ls, job_ref=job_ref)
        if reason == 'backendError':
            return GoogleCloudBackendError(message, error, error_ls, job_ref=job_ref)
        if reason == 'invalidParameter':
            return GoogleCloudInvalidParameterError(message, error, error_ls, job_ref=job_ref)
        if reason == 'badRequest':
            return GoogleCloudBadRequestError(message, error, error_ls, job_ref=job_ref)
        if reason == 'invalidCredentials':
            return GoogleCloudInvalidCredentialsError(message, error, error_ls, job_ref=job_ref)
        if reason == 'insufficientPermissions':
            return GoogleCloudInsufficientPermissionsError(message, error, error_ls, job_ref=job_ref)
        if reason == 'userRateLimitExceeded':
            return GoogleCloudUserRateLimitExceededError(message, error, error_ls, job_ref=job_ref)
        if reason == 'quotaExceeded':
            return GoogleCloudQuotaExceededError(message, error, error_ls, job_ref=job_ref)

        # We map the less interesting errors to GoogleCloudStorageServiceError.
        return GoogleCloudServiceError(message, error, error_ls, job_ref=job_ref)


class GoogleCloudServiceError(GoogleCloudError):
    """Base class of CloudStorage-specific error responses.

    The BigQuery server received request and returned an error.
    """

    def __init__(self, message, error, error_list, job_ref=None, *args, **kwds):
        """Initializes a CloudStorageServiceError.

        :param message: A user-facing error message.
        :param error: The error dictionary, code may inspect the 'reason' key.
        :param error_list: A list of additional entries, for example a load job may contain multiple errors here for each error encountered during processing.
        :param job_ref: Optional job reference.
        :return:
            A BigQueryError instance.
        """
        super(GoogleCloudServiceError, self).__init__(message, *args, **kwds)
        self.error = error
        self.error_list = error_list
        self.job_ref = job_ref

    def __repr__(self):
        return '%s: error=%s, error_list=%s, job_ref=%s' % (self.__class__.__name__, self.error, self.error_list, self.job_ref)


class GoogleCloudAuthorizationError(GoogleCloudServiceError):
    """403 error wrapper"""
    pass


class GoogleCloudNotFoundError(GoogleCloudServiceError):
    """404 error wrapper"""
    pass


class GoogleCloudBackendError(GoogleCloudServiceError):
    pass


class GoogleCloudInterfaceError(GoogleCloudServiceError):
    pass


class GoogleCloudRateLimitExceededError(GoogleCloudServiceError):
    pass


class GoogleCloudDailyLimitExceededError(GoogleCloudServiceError):
    pass


class GoogleCloudInvalidParameterError(GoogleCloudServiceError):
    pass


class GoogleCloudInvalidCredentialsError(GoogleCloudServiceError):
    pass


class GoogleCloudBadRequestError(GoogleCloudServiceError):
    pass


class GoogleCloudInsufficientPermissionsError(GoogleCloudServiceError):
    pass


class GoogleCloudUserRateLimitExceededError(GoogleCloudServiceError):
    pass


class GoogleCloudQuotaExceededError(GoogleCloudServiceError):
    pass
