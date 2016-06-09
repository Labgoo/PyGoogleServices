__author__ = 'krakover'

import unittest2 as unittest
import httplib2
from googleapiclient.discovery import build
from oauth2client.contrib.gce import AppAssertionCredentials
from googleservices.shared.utils import get_google_credentials

class Test(unittest.TestCase):
    def testGetDocumentById_documentWithIdExists_returnCorrectDocument(self):
        credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/bigquery')
        http = credentials.authorize(httplib2.Http())
        return build('bigquery', 'v2', http=http)