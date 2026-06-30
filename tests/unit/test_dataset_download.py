# coding=utf-8
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "../../src")

from kaggle.api.kaggle_api_extended import KaggleApi


class TestDatasetDownload(unittest.TestCase):

    def setUp(self):
        self.api = KaggleApi.__new__(KaggleApi)
        self.api.config_values = {"username": "testuser"}

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    @patch("zipfile.ZipFile")
    @patch.object(KaggleApi, "download_needed", return_value=False)
    @patch.object(KaggleApi, "download_file")
    @patch.object(KaggleApi, "build_kaggle_client")
    def test_dataset_download_cached_unzip(
        self, mock_client, mock_download_file, mock_download_needed, mock_zipfile, mock_remove, mock_exists
    ):
        """Case 1: When dataset is cached (download_needed is False) and unzip=True,
        it should still extract the existing ZIP and remove it, without downloading again.
        """
        mock_kaggle = MagicMock()
        mock_response = MagicMock()
        mock_kaggle.datasets.dataset_api_client.download_dataset.return_value = mock_response
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_kaggle)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        path = os.path.normpath("/tmp/dummy")

        # Call method with unzip=True, force=False
        self.api.dataset_download_files("owner/my-dataset", path=path, unzip=True, force=False)

        # Verify download_file was NOT called
        mock_download_file.assert_not_called()

        # Verify zipfile.ZipFile was called to extract the file
        expected_outfile = os.path.join(path, "my-dataset.zip")
        mock_zipfile.assert_called_once()
        called_args = mock_zipfile.call_args[0][0]
        self.assertEqual(os.path.normpath(called_args), expected_outfile)

        # Verify extractall and remove were called
        mock_zipfile().__enter__().extractall.assert_called_once_with(path)
        mock_remove.assert_called_once()
        self.assertEqual(os.path.normpath(mock_remove.call_args[0][0]), expected_outfile)

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    @patch("zipfile.ZipFile")
    @patch.object(KaggleApi, "download_needed", return_value=True)
    @patch.object(KaggleApi, "download_file")
    @patch.object(KaggleApi, "build_kaggle_client")
    def test_dataset_download_fresh_unzip(
        self, mock_client, mock_download_file, mock_download_needed, mock_zipfile, mock_remove, mock_exists
    ):
        """Case 2: When dataset is not cached (download_needed is True) and unzip=True,
        it should download the ZIP, extract it, and remove it.
        """
        mock_kaggle = MagicMock()
        mock_response = MagicMock()
        mock_kaggle.datasets.dataset_api_client.download_dataset.return_value = mock_response
        mock_client.return_value.__enter__ = MagicMock(return_value=mock_kaggle)
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        path = os.path.normpath("/tmp/dummy")

        # Call method with unzip=True, force=False
        self.api.dataset_download_files("owner/my-dataset", path=path, unzip=True, force=False)

        # Verify download_file was called
        mock_download_file.assert_called_once()

        # Verify zipfile.ZipFile was called to extract the file
        expected_outfile = os.path.join(path, "my-dataset.zip")
        mock_zipfile.assert_called_once()
        called_args = mock_zipfile.call_args[0][0]
        self.assertEqual(os.path.normpath(called_args), expected_outfile)

        # Verify extractall and remove were called
        mock_zipfile().__enter__().extractall.assert_called_once_with(path)
        mock_remove.assert_called_once()
        self.assertEqual(os.path.normpath(mock_remove.call_args[0][0]), expected_outfile)


if __name__ == "__main__":
    unittest.main()
