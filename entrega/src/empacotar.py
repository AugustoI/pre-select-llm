"""Build the portable handoff ZIP, excluding local history, environments and caches."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def delivery_files():
    allowed = {'dados', 'docs', 'notebooks', 'src', 'tests'}
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if '__pycache__' in relative.parts or '.ipynb_checkpoints' in relative.parts:
            continue
        if relative.parts[0] in allowed or relative.as_posix() in {'README.md', 'requirements.txt', '.gitattributes'}:
            yield path


def main():
    files = list(delivery_files())
    manifest = {'algorithm': 'sha256', 'files': {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}
    index = ROOT / 'MANIFESTO_SHA256.json'
    index.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    folder = ROOT.parent / 'distribuicao'
    folder.mkdir(exist_ok=True)
    destination = folder / 'PreSelect_Entrega_6_Modelos.zip'
    temporary = destination.with_suffix('.partial')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files + [index]:
            archive.write(path, 'PreSelect_Entrega/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise IOError('ZIP final inválido.')
    temporary.replace(destination)
    print(f'{destination}\n{len(files) + 1} arquivos; {destination.stat().st_size / 2**20:.2f} MiB')


if __name__ == '__main__':
    main()
