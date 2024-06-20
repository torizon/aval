import unittest

from common import parse_device_id

device_id_dict = {
    "verdin-imx8mm-07214001-9334fa": "imx8mm",
    "verdin-imx8mp-15247251-0bd6e5": "imx8mp",
    "verdin-am62-15133530-24fe44": "am62",
    "colibri-imx8x-07203041-b5464c": "imx8x",
    "colibri-imx7-emmc-15149329-6f39ce": "imx7",
    "colibri-imx6-15054304-e259ec": "imx6",
}


class TestCommon(unittest.TestCase):
    def test_parse_device_id(self):
        for device_id, expected in device_id_dict.items():
            with self.subTest(device_id=device_id):
                self.assertEqual(parse_device_id(device_id), expected)
