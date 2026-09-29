"""Local-only ComfyUI video provider. No cloud routing or paid fallback."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ALLOWED_NODES = {
    'UnetLoaderGGUF', 'CLIPLoaderGGUF', 'UNETLoader', 'CLIPLoader', 'CLIPTextEncode',
    'VAELoader', 'LoadImage', 'Wan22ImageToVideoLatent', 'WanFirstLastFrameToVideo',
    'WanImageToVideo', 'ModelSamplingSD3', 'KSampler', 'KSamplerAdvanced',
    'VAEDecode', 'VAEDecodeTiled', 'CreateVideo', 'SaveVideo', 'SaveImage',
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('LOCAL_VIDEO_PROVIDER refuses redirects')


class LocalVideoProvider:
    def __init__(self, url: str | None = None):
        url = url or os.environ.get('LOCAL_COMFYUI_URL', 'http://127.0.0.1:8188')
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise ValueError('LOCAL_VIDEO_PROVIDER only accepts a loopback HTTP ComfyUI URL')
        self.url = url.rstrip('/')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, endpoint, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + endpoint, data=data,
                                        headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()[:8000]) from error

    def health(self):
        return {'provider': 'comfyui', 'local_only': True, 'cloud_fallback': False,
                'system_stats': self.request('/system_stats')}

    @staticmethod
    def validate(workflow):
        if not isinstance(workflow, dict) or not workflow or 'nodes' in workflow:
            raise ValueError('Expected a nonempty ComfyUI API workflow')
        for node in workflow.values():
            if not isinstance(node, dict):
                raise ValueError("Each node must be an object")
            if node.get('class_type') not in ALLOWED_NODES:
                raise ValueError(f'Node is not approved for local video: {node.get("class_type")}')
            if not isinstance(node.get('inputs'), dict):
                raise ValueError('Each node needs an inputs object')
        if not any(n['class_type'] in ('SaveVideo', 'SaveImage') for n in workflow.values()):
            raise ValueError('Workflow needs a real output node')

    def submit(self, workflow):
        self.validate(workflow)
        result = self.request('/prompt', {'prompt': workflow, 'client_id': str(uuid.uuid4())})
        if result.get('node_errors') or not result.get('prompt_id'):
            raise RuntimeError(json.dumps(result, ensure_ascii=False))
        return {'status': 'submitted', 'provider': 'comfyui', **result,
                'animation_qa': 'NOT_EVALUATED'}

    def status(self, prompt_id):
        safe = urllib.parse.quote(prompt_id, safe='')
        history = self.request('/history/' + safe)
        if prompt_id in history:
            result = history[prompt_id]
            return {'prompt_id': prompt_id, 'status': result.get('status'),
                    'outputs': result.get('outputs'), 'animation_qa': 'NOT_EVALUATED'}
        return {'prompt_id': prompt_id, 'status': 'not_in_history', 'queue': self.request('/queue')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['health', 'submit', 'status'])
    parser.add_argument('--url')
    parser.add_argument('--workflow', type=Path)
    parser.add_argument('--prompt-id')
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    provider = LocalVideoProvider(args.url)
    if args.action == 'health':
        result = provider.health()
    elif args.action == 'submit':
        if not args.workflow: parser.error('--workflow is required')
        result = provider.submit(json.loads(args.workflow.read_text()))
    else:
        if not args.prompt_id: parser.error('--prompt-id is required')
        result = provider.status(args.prompt_id)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
