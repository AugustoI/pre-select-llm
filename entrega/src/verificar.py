"""Offline validation of the six original results and the delivered consolidated data."""
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from bundles import read_result
from unificar import compatible_samples, merge

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    root = Path(root)
    sample = root / 'dados/amostras/amostra_preselect.zip'
    original = sample.with_name('manifesto_quatro_originais.json')
    combined, docs, manifests = compatible_samples(sample, original)
    paths = sorted((root / 'dados/resultados_por_modelo').glob('resultado_*.zip'))
    expected_counts = {'hellaswag': 10042, 'arc_easy': 2376, 'boolq': 3270}
    evidence = []
    for path in paths:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP corrompido: ' + path.name)
            identity = json.loads(archive.read('result.json'))['sample_id']
        metadata, benchmark, rows = read_result(path, manifests[identity], docs)
        model = metadata['model']
        receipt_path = root / 'dados/preselect_estado' / identity[:16] / (model.replace('/', '__') + '.concluido.json')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        required = {'status': 'complete', 'model': model, 'sample_id': identity,
                    'protocol_id': combined['protocol_id'], 'revision': metadata['revision'],
                    'documents': len(docs), 'core_sha256': metadata['core_sha256'], 'zip_sha256': sha}
        if any(receipt.get(key) != value for key, value in required.items()):
            raise ValueError('Registro de conclusão incompatível: ' + model)
        for task, count in expected_counts.items():
            if benchmark['n_samples'][task] != {'original': count, 'effective': count}:
                raise ValueError('Benchmark incompleto: ' + model + '/' + task)
        evidence.append({'model': model, 'documents': len(rows), 'sha256': sha,
                         'capability': benchmark['score'], 'benchmark_examples': expected_counts,
                         'scored_tokens': sum(r['n_scored_tokens'] for r in rows.values())})
    with tempfile.TemporaryDirectory() as temporary:
        recomputed = merge(sample, paths, Path(temporary) / 'recomputed.zip', original)
    # Split JSONL bytes on newlines; str.splitlines also splits Unicode characters inside valid texts.
    stored = [json.loads(line) for line in (root / 'dados/consolidado/documentos_forca_preditiva.jsonl').read_bytes().splitlines()]
    if stored != recomputed:
        raise ValueError('O consolidado difere do recálculo dos seis ZIPs.')
    report = {'status': 'validado', 'documents': len(docs), 'models': len(evidence),
              'bpc_values': len(docs) * len(evidence), 'domains': len({d['domain'] for d in docs}),
              'comparable_pairs_per_document': sorted({r['comparable_pairs'] for r in stored}),
              'protocol_id': combined['protocol_id'], 'source_sample_ids': list(manifests),
              'checks': ['ZIP CRC', 'completion receipt SHA256 and identity', 'document hashes and IDs',
                         'exact model revisions and protocol', 'full benchmark example counts',
                         'complete token coverage and BPC formula', 'exact recomputation of consolidated rows'],
              'results': evidence}
    return report


if __name__ == '__main__':
    report = verify()
    target = ROOT / 'docs/verificacao.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"VALIDADO: {report['documents']} documentos, {report['models']} modelos, {report['bpc_values']} BPCs.")
