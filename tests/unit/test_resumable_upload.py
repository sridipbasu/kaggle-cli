# coding=utf-8
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from kaggle.api.kaggle_api_extended import KaggleApi
from kaggle.models.kaggle_models_extended import ResumableUploadResult


class TestResumableUpload(unittest.TestCase):

    def setUp(self):
        self.api = KaggleApi.__new__(KaggleApi)

    def test_get_bytes_already_uploaded_no_range(self):
        response = MagicMock()
        response.headers = {}
        bytes_uploaded = self.api._get_bytes_already_uploaded(response, quiet=True)
        self.assertEqual(bytes_uploaded, -1)

        result = ResumableUploadResult.Incomplete(bytes_uploaded)
        self.assertEqual(result.bytes_uploaded, 0)
        self.assertEqual(result.start_at, 0)

    def test_get_bytes_already_uploaded_range_zero(self):
        response = MagicMock()
        response.headers = {"Range": "bytes=0-0"}
        bytes_uploaded = self.api._get_bytes_already_uploaded(response, quiet=True)
        self.assertEqual(bytes_uploaded, 0)

        result = ResumableUploadResult.Incomplete(bytes_uploaded)
        self.assertEqual(result.bytes_uploaded, 0)
        self.assertEqual(result.start_at, 1)

    def test_get_bytes_already_uploaded_range_mid(self):
        response = MagicMock()
        response.headers = {"Range": "bytes=0-499"}
        bytes_uploaded = self.api._get_bytes_already_uploaded(response, quiet=True)
        self.assertEqual(bytes_uploaded, 499)

        result = ResumableUploadResult.Incomplete(bytes_uploaded)
        self.assertEqual(result.bytes_uploaded, 499)
        self.assertEqual(result.start_at, 500)

    def test_get_bytes_already_uploaded_malformed_range(self):
        response = MagicMock()
        response.headers = {"Range": "bytes=abc"}
        bytes_uploaded = self.api._get_bytes_already_uploaded(response, quiet=True)
        self.assertIsNone(bytes_uploaded)

    @patch("requests.Session")
    def test_resume_upload_no_range_header(self, mock_session):
        # Case: status query returns 308 with no Range header
        mock_response = MagicMock()
        mock_response.status_code = 308
        mock_response.headers = {}
        
        session_instance = mock_session.return_value
        session_instance.put.return_value = mock_response

        result = self.api._resume_upload("path/to/file", "http://upload.url", 1000, quiet=True)
        self.assertEqual(result.result, ResumableUploadResult.INCOMPLETE)
        self.assertEqual(result.bytes_uploaded, 0)
        self.assertEqual(result.start_at, 0)

    @patch("requests.Session")
    def test_resume_upload_range_zero(self, mock_session):
        # Case: status query returns 308 with Range: bytes=0-0
        mock_response = MagicMock()
        mock_response.status_code = 308
        mock_response.headers = {"Range": "bytes=0-0"}
        
        session_instance = mock_session.return_value
        session_instance.put.return_value = mock_response

        result = self.api._resume_upload("path/to/file", "http://upload.url", 1000, quiet=True)
        self.assertEqual(result.result, ResumableUploadResult.INCOMPLETE)
        self.assertEqual(result.bytes_uploaded, 0)
        self.assertEqual(result.start_at, 1)

    @patch("requests.Session")
    def test_resume_upload_range_mid(self, mock_session):
        # Case: status query returns 308 with Range: bytes=0-499
        mock_response = MagicMock()
        mock_response.status_code = 308
        mock_response.headers = {"Range": "bytes=0-499"}
        
        session_instance = mock_session.return_value
        session_instance.put.return_value = mock_response

        result = self.api._resume_upload("path/to/file", "http://upload.url", 1000, quiet=True)
        self.assertEqual(result.result, ResumableUploadResult.INCOMPLETE)
        self.assertEqual(result.bytes_uploaded, 499)
        self.assertEqual(result.start_at, 500)

    @patch("requests.Session")
    def test_resume_upload_complete(self, mock_session):
        # Case: status query returns 200 (upload already complete)
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        session_instance = mock_session.return_value
        session_instance.put.return_value = mock_response

        result = self.api._resume_upload("path/to/file", "http://upload.url", 1000, quiet=True)
        self.assertEqual(result.result, ResumableUploadResult.COMPLETE)

    @patch("requests.Session")
    def test_resume_upload_expired(self, mock_session):
        # Case: status query returns 404 (upload expired/failed)
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        session_instance = mock_session.return_value
        session_instance.put.return_value = mock_response

        result = self.api._resume_upload("path/to/file", "http://upload.url", 1000, quiet=True)
        self.assertEqual(result.result, ResumableUploadResult.FAILED)


if __name__ == "__main__":
    unittest.main()
