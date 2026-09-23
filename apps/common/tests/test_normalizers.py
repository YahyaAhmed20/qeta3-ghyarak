from django.test import SimpleTestCase

from apps.common.normalizers import normalize_vin


class NormalizeVINTests(SimpleTestCase):

    def test_normalize_vin_uppercases_value(self):
        result = normalize_vin("1hgcm82633a123456")

        self.assertEqual(result, "1HGCM82633A123456")

    def test_normalize_vin_removes_spaces(self):
        result = normalize_vin("1hg cm826 33a123456")

        self.assertEqual(result, "1HGCM82633A123456")

    def test_normalize_vin_handles_empty_value(self):
        self.assertEqual(normalize_vin(""), "")

    def test_normalize_vin_handles_none(self):
        self.assertEqual(normalize_vin(None), "")