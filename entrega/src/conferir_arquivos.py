"""Verify the checksum manifest without executing notebooks or installing packages."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / 'MANIFESTO_SHA256.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['files'].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Arquivo ausente ou caminho inválido: ' + relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Arquivo modificado: ' + relative)
    print(f"Hashes conferidos: {len(manifest['files'])} arquivos.")


if __name__ == '__main__':
    check()
