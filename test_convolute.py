import unittest
import convolute
import yaml
import toml

# Mock data for the tests
pid4_map_data = {
    "verdin-imx8mp": {
        "pid4": [
            {"id": 1, "soc_npu": True, "soc_gpu": False},
            {"id": 2, "soc_npu": True},
            {"id": 3, "soc_npu": False, "soc_gpu": True},
        ]
    }
}

# Mock TOML data as a string
mock_toml_data = """
[soc_udt]
soc_udt_name = "verdin-imx8mp"
soc_properties = ["soc_npu", "soc_gpu"]
"""

# Mock YAML data as a string
mock_yaml_data = """
verdin-imx8mp:
  pid4:
    - id: 1
      soc_npu: true
      soc_gpu: false
    - id: 2
      soc_npu: true
    - id: 3
      soc_npu: false
      soc_gpu: true
"""


class TestConvolute(unittest.TestCase):

    def test_get_pid4_list(self):
        soc = "verdin-imx8mp"
        expected_pid4_list = [
            1,
            2,
            3,
        ]  # All PIDs, as we're not filtering by properties

        result = convolute.get_pid4_list(soc, pid4_map_data)
        self.assertEqual(result, expected_pid4_list)

    def test_get_pid4_list_with_device_config(self):
        # Parse the mock TOML and YAML data into dictionaries
        device_config_data = toml.loads(mock_toml_data)
        pid4_map_data = yaml.safe_load(mock_yaml_data)

        # Only the first and third entries have both 'soc_npu' and 'soc_gpu' properties
        expected_pid4_list = [1, 3]

        result = convolute.get_pid4_list_with_device_config(
            device_config_data, pid4_map_data
        )
        self.assertEqual(result, expected_pid4_list)


if __name__ == "__main__":
    unittest.main()
