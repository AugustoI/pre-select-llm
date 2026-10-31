"""Portable sample and per-model result validation. Standard library only."""
import hashlib
import json
import math
import os
import zipfile
from pathlib import Path


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return hash_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2).encode()


def rows_bytes(rows):
    return ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows).encode()


def atomic_zip(path, files):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.partial')
    with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(tmp) as archive:
        if archive.testzip() is not None:
            raise IOError('ZIP inválido; resultado não publicado.')
    os.replace(tmp, path)


def read_sample(path):
    with zipfile.ZipFile(path) as archive:
        raw = archive.read('documents.jsonl')
        manifest = json.loads(archive.read('sample.json'))
    if hash_bytes(raw) != manifest['documents_sha256']:
        raise ValueError('O texto da amostra não corresponde ao hash salvo.')
    if fingerprint(manifest['protocol']) != manifest['protocol_id']:
        raise ValueError('Protocolo da amostra alterado.')
    if fingerprint({k: v for k, v in manifest.items() if k != 'sample_id'}) != manifest['sample_id']:
        raise ValueError('Manifesto da amostra alterado.')
    docs = [json.loads(line) for line in raw.splitlines()]
    if len(docs) != manifest['count'] or not docs or len({d['document_id'] for d in docs}) != len(docs):
        raise ValueError('Quantidade ou IDs inválidos na amostra.')
    for doc in docs:
        if hash_bytes(doc['text'].encode()) != doc['text_sha256'] or len(doc['text']) != doc['n_chars']:
            raise ValueError('Texto/contagem alterados: ' + doc['document_id'])
    return manifest, docs


def validate_result(manifest, docs, metadata, benchmark, rows):
    model = metadata['model']
    if model not in manifest['model_revisions']:
        raise ValueError('Modelo fora da suíte: ' + model)
    for key in ('sample_id', 'protocol_id'):
        if metadata.get(key) != manifest[key]:
            raise ValueError('Pacote de outra amostra/protocolo: ' + key)
    if metadata.get('revision') != manifest['model_revisions'][model]:
        raise ValueError('Checkpoint do modelo diferente.')
    if metadata.get('dtype') != manifest['protocol']['dtype']:
        raise ValueError('Precisão numérica diferente.')
    if metadata.get('core_sha256') != manifest['protocol']['core_sha256']:
        raise ValueError('Implementação de BPC/benchmark diferente.')
    if benchmark.get('limit') != manifest['protocol']['benchmark_limit']:
        raise ValueError('Benchmark parcial ou diferente do protocolo.')
    task_scores = benchmark.get('per_task', {})
    if set(task_scores) != set(manifest['protocol']['benchmarks']):
        raise ValueError('Tarefas de avaliação diferentes.')
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in task_scores.values()):
        raise ValueError('Métrica de benchmark inválida.')
    expected_mean = sum(task_scores.values()) / len(task_scores)
    if not math.isfinite(benchmark['score']) or abs(benchmark['score'] - expected_mean) > 1e-12:
        raise ValueError('Média de benchmark inconsistente.')
    by_id = {r['document_id']: r for r in rows}
    if len(by_id) != len(rows) or set(by_id) != {d['document_id'] for d in docs}:
        raise ValueError('BPC faltando, duplicado ou de outro conjunto de documentos.')
    for doc in docs:
        row = by_id[doc['document_id']]
        if (row.get('text_sha256') != doc['text_sha256'] or row.get('n_chars') != doc['n_chars']
                or row.get('n_tokens', 0) <= 0 or row.get('n_tokens') != row.get('n_scored_tokens')):
            raise ValueError('Texto ou cobertura inválidos: ' + doc['document_id'])
        expected_bpc = row['nll_sum'] / (doc['n_chars'] * math.log(2))
        if not math.isfinite(row['bpc']) or row['bpc'] < 0 or not math.isfinite(expected_bpc) or not math.isclose(row['bpc'], expected_bpc, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError('BPC inválido: ' + doc['document_id'])
    return by_id


def read_result(path, manifest, docs):
    with zipfile.ZipFile(path) as archive:
        metadata = json.loads(archive.read('result.json'))
        benchmark = json.loads(archive.read('benchmark.json'))
        rows = [json.loads(line) for line in archive.read('bpc.jsonl').splitlines()]
    by_id = validate_result(manifest, docs, metadata, benchmark, rows)
    return metadata, benchmark, by_id
