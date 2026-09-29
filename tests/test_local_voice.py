import unittest
from pathlib import Path
from unittest.mock import patch

from anime_knowledge_video.local_voice import synthesize, voice_preset
from anime_knowledge_video.mcp_lite import handle


class LocalVoiceTests(unittest.TestCase):
    def test_invalid_requests_stop_before_loading_native_runtime(self):
        with patch('anime_knowledge_video.local_voice.health') as health:
            for args in [dict(text='', speaker='male'), dict(text='a', speaker='unknown'),
                         dict(text='a', speaker='male', max_duration_sec=0),
                         dict(text='a', speaker='male', output_dir='../outside'),
                         dict(text='a', speaker='male', output_dir=str(Path('/tmp/escape')))]:
                with self.assertRaises(ValueError):
                    synthesize(**args)
            health.assert_not_called()

    def test_missing_runtime_is_reported_without_fallback(self):
        with patch('anime_knowledge_video.local_voice.health', return_value={
                'ready': False, 'checks': {'voicevox_core': False}}):
            with self.assertRaisesRegex(RuntimeError, 'voicevox_core'):
                synthesize('こんにちは。', 'female')

    def test_presets_cannot_be_mutated_by_a_caller(self):
        preset = voice_preset('male')
        preset['pitch'] = 100
        self.assertEqual(voice_preset('male')['pitch'], 0)

    def test_mcp_routes_voice_and_returns_actionable_errors(self):
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {
            'name': 'synthesize_local_voice', 'arguments': {'text': '今。', 'speaker': 'female'}}}
        with patch('anime_knowledge_video.mcp_lite.synthesize_voice', return_value={'status': 'synthesized'}) as synth:
            result = handle(request)
            synth.assert_called_once_with(text='今。', speaker='female')
            self.assertIn('synthesized', result['result']['content'][0]['text'])
        request['params']['arguments']['speaker'] = 'unknown'
        self.assertTrue(handle(request)['result']['isError'])


if __name__ == '__main__':
    unittest.main()
