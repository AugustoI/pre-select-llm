"""CPU/local preparation: stream source files without saving full shards."""
import argparse
import io
import itertools
import json
import random
import urllib.request
from collections import Counter
from pathlib import Path
import core
from bundles import atomic_zip, fingerprint, hash_bytes, json_bytes, rows_bytes, read_sample

MODELS = ['EleutherAI/pythia-160m-deduped', 'EleutherAI/pythia-410m-deduped',
          'EleutherAI/pythia-1b-deduped', 'EleutherAI/gpt-neo-1.3B']


def stream_rows(url, limit, expected=None):
    import zstandard
    request = urllib.request.Request(url, headers={'If-Match': expected['etag']} if expected and expected.get('etag') else {})
    with urllib.request.urlopen(request, timeout=120) as response:
        with zstandard.ZstdDecompressor().stream_reader(response) as reader:
            with io.TextIOWrapper(reader, encoding='utf-8') as text:
                for number, line in enumerate(itertools.islice(text, limit), 1):
                    yield number, json.loads(line)


def prepare(output, domains=50, per_domain=20, shards=4, scan=50000, seed=42):
    output = Path(output)
    if output.exists():
        manifest, docs = read_sample(output)
        expected = dict(domains=domains, per_domain=per_domain, shards=shards, scan=scan, seed=seed)
        if manifest['sampling'] != expected:
            raise ValueError('Já existe outra amostra nesse caminho. Escolha outro arquivo de saída.')
        print('Amostra já validada:', output, len(docs), 'documentos')
        return
    urls = core.original_sources(shards, seed)
    sources = []
    for url in urls:
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=60) as response:
            sources.append({'url': url, 'etag': response.headers.get('ETag'), 'bytes': int(response.headers['Content-Length'])})
    counts = Counter()
    for i, source in enumerate(sources, 1):
        print(f'Contando domínios: fonte {i}/{len(sources)} (streaming; sem gravar shard)', flush=True)
        for line, row in stream_rows(source['url'], scan, source):
            doc = core.normalize_document(row, source['url'], line)
            if doc:
                counts[doc['domain']] += 1
    selected = sorted(counts, key=lambda d: (-counts[d], d))[:domains]
    buckets, seen, rng = {d: [] for d in selected}, Counter(), random.Random(seed)
    for i, source in enumerate(sources, 1):
        print(f'Amostrando: fonte {i}/{len(sources)}', flush=True)
        for line, row in stream_rows(source['url'], scan, source):
            doc = core.normalize_document(row, source['url'], line)
            if not doc or doc['domain'] not in buckets:
                continue
            domain = doc['domain']
            seen[domain] += 1
            bucket = buckets[domain]
            if len(bucket) < per_domain:
                bucket.append(doc)
            else:
                j = rng.randrange(seen[domain])
                if j < per_domain:
                    bucket[j] = doc
    docs = sorted(itertools.chain.from_iterable(buckets.values()), key=lambda d: d['document_id'])
    if not docs:
        raise ValueError('Nenhum documento elegível encontrado.')
    revisions = {}
    for model in MODELS:
        with urllib.request.urlopen('https://huggingface.co/api/models/' + model, timeout=60) as response:
            revisions[model] = json.load(response)['sha']
    protocol = {'context': 1024, 'stride': 512, 'dtype': 'bfloat16', 'seed': seed,
                'benchmarks': {'hellaswag': 'acc_norm,none', 'arc_easy': 'acc_norm,none', 'boolq': 'acc,none'},
                'benchmark_limit': None, 'num_fewshot': 0, 'lm_eval_version': '0.4.9.2',
                'core_sha256': hash_bytes(Path(core.__file__).read_bytes()),
                'method': 'isolated documents, BOS/EOS prefix, no truncation, NLL / (Unicode characters * ln(2))'}
    data = rows_bytes(docs)
    manifest = {'format': 1, 'documents_sha256': hash_bytes(data), 'count': len(docs),
                'protocol': protocol, 'protocol_id': fingerprint(protocol), 'model_revisions': revisions,
                'sampling': dict(domains=domains, per_domain=per_domain, shards=shards, scan=scan, seed=seed),
                'sources': sources, 'sample_per_domain': {d: len(buckets[d]) for d in selected},
                'scope': 'new sample from scanned prefixes of DCLM-refinedweb source shards; not exact author sample'}
    manifest['sample_id'] = fingerprint(manifest)
    atomic_zip(output, {'documents.jsonl': data, 'sample.json': json_bytes(manifest)})
    read_sample(output)
    print(f'Pronto: {output} | {len(docs)} documentos | {output.stat().st_size / 2**20:.2f} MiB', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida', default='amostra_preselect.zip')
    p.add_argument('--dominios', type=int, default=50)
    p.add_argument('--por-dominio', type=int, default=20)
    p.add_argument('--shards', type=int, default=4)
    p.add_argument('--linhas-por-shard', type=int, default=50000)
    args = p.parse_args()
    prepare(args.saida, args.dominios, args.por_dominio, args.shards, args.linhas_por_shard)
