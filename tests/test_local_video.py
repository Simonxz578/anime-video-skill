import unittest

from anime_knowledge_video.local_video import LocalVideoProvider


class LocalVideoTests(unittest.TestCase):
    def test_cloud_and_url_credentials_are_rejected(self):
        for url in ['https://cloud.comfy.org', 'http://192.168.1.2:8188',
                    'http://127.0.0.1.evil.test:8188', 'http://secret@localhost:8188',
                    'http://localhost:8188/?token=x']:
            with self.assertRaises(ValueError):
                LocalVideoProvider(url)
        self.assertEqual(LocalVideoProvider().url, 'http://127.0.0.1:8188')

    def test_unapproved_provider_node_is_rejected(self):
        with self.assertRaises(ValueError):
            LocalVideoProvider.validate({'1': {'class_type': 'PaidVideoAPI', 'inputs': {}}})

    def test_no_output_or_ui_graph_is_not_submitted(self):
        for graph in [{}, {'nodes': []}, {'1': {'class_type': 'LoadImage', 'inputs': {}}}]:
            with self.assertRaises(ValueError):
                LocalVideoProvider.validate(graph)


if __name__ == '__main__':
    unittest.main()
