"""Merge model ZIPs on CPU. No Torch, GPU or third-party package required."""
import argparse
import csv
import io
import itertools
import json
import zipfile
from pathlib import Path
from bundles import read_sample, read_result, atomic_zip, json_bytes, rows_bytes, fingerprint


def compatible_samples(sample, base_manifest):
    """Validate each run's identity without rewriting metadata in old results."""
    additional, docs = read_sample(sample)
    original = json.loads(Path(base_manifest).read_text(encoding='utf-8'))
    # Reconstruct the original sample in memory using the exact shared document bytes.
    with zipfile.ZipFile(sample) as archive:
        raw = archive.read('documents.jsonl')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('documents.jsonl', raw)
        archive.writestr('sample.json', json_bytes(original))
    buffer.seek(0)
    original, original_docs = read_sample(buffer)
    if additional.get('extension_of') != original['sample_id']:
        raise ValueError('Extensão não corresponde à execução original.')
    if additional['protocol_id'] != original['protocol_id'] or docs != original_docs:
        raise ValueError('Documentos ou protocolo diferentes entre as execuções.')
    if set(original['model_revisions']) & set(additional['model_revisions']):
        raise ValueError('Modelos repetidos entre as execuções.')
    if len(original['model_revisions']) != 4 or len(additional['model_revisions']) != 2:
        raise ValueError('Esperados quatro modelos originais e dois adicionais.')
    combined = {k: v for k, v in original.items() if k != 'sample_id'}
    combined['model_revisions'] = {**original['model_revisions'], **additional['model_revisions']}
    combined['source_sample_ids'] = [original['sample_id'], additional['sample_id']]
    combined['sample_id'] = fingerprint(combined)
    manifests = {m['sample_id']: m for m in (original, additional)}
    return combined, docs, manifests


def merge(sample, inputs, output, base_manifest=None):
    if base_manifest is None:
        base_manifest = Path(sample).with_name('manifesto_quatro_originais.json')
    manifest, docs, manifests = compatible_samples(sample, base_manifest)
    results, capabilities, reports = {}, {}, {}
    versions = None
    for path in inputs:
        with zipfile.ZipFile(path) as archive:
            identity = json.loads(archive.read('result.json')).get('sample_id')
        if identity not in manifests:
            raise ValueError('ZIP de outra amostra/execução: ' + str(path))
        metadata, benchmark, by_id = read_result(path, manifests[identity], docs)
        model = metadata['model']
        if model in results:
            raise ValueError('Dois ZIPs do mesmo modelo: ' + model)
        current_versions = {k: metadata['packages'][k] for k in ('transformers', 'lm_eval', 'tokenizers', 'datasets')}
        if versions is not None and versions != current_versions:
            raise ValueError('Pacotes calculados com versões de bibliotecas diferentes.')
        versions = current_versions
        results[model], capabilities[model] = by_id, benchmark['score']
        reports[model] = {'metadata': metadata, 'benchmark': benchmark}
    missing = set(manifest['model_revisions']) - set(results)
    if missing:
        raise ValueError('Faltam resultados: ' + ', '.join(sorted(missing)))
    if len(results) < 2:
        raise ValueError('Força preditiva precisa de pelo menos dois modelos.')
    ordered = sorted(capabilities, key=lambda m: (capabilities[m], m))
    pairs = [(a, b) for a, b in itertools.combinations(ordered, 2) if capabilities[a] != capabilities[b]]
    if not pairs:
        raise ValueError('Todos os modelos empataram: força preditiva indefinida.')
    tied = len(ordered) * (len(ordered) - 1) // 2 - len(pairs)
    combined = []
    for doc in docs:
        values = {m: results[m][doc['document_id']]['bpc'] for m in ordered}
        concordant = sum(values[weak] > values[strong] for weak, strong in pairs)
        combined.append({**doc, 'predictive_strength': concordant / len(pairs), 'concordant_pairs': concordant,
                         'comparable_pairs': len(pairs), 'benchmark_tied_pairs': tied,
                         **{'bpc__' + m: values[m] for m in ordered}})
    combined.sort(key=lambda r: (-r['predictive_strength'], r['document_id']))
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=[k for k in combined[0] if k != 'text'], extrasaction='ignore')
    writer.writeheader()
    writer.writerows(combined)
    output = Path(output)
    atomic_zip(output, {'documentos_forca_preditiva.jsonl': rows_bytes(combined),
                       'documentos_resumo.csv': text.getvalue().encode('utf-8-sig'),
                       'ranking_e_benchmarks.json': json_bytes(reports), 'sample.json': json_bytes(manifest),
                       'manifestos_execucoes.json': json_bytes(manifests),
                       'LEIA_ME.txt': ('JSONL contém os textos integrais, origem, BPCs e força entre 0 e 1. CSV omite o texto.\n'
                                       'Força = fração de pares em que maior capacidade corresponde a menor BPC.\n'
                                       'Empates de capacidade são excluídos e reportados. Empates de BPC não contam.\n'
                                       'Nova amostra e suíte reduzida; não são rótulos originais dos autores.\n').encode()})
    print(f'Unificação concluída: {len(combined)} documentos × {len(results)} modelos.\n{output.resolve()}')
    return combined


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--amostra', default='amostra_preselect.zip')
    p.add_argument('--manifesto-original', default='manifesto_quatro_originais.json')
    p.add_argument('--resultados', default='resultados', help='Pasta com os ZIPs baixados de cada modelo')
    p.add_argument('--saida', default='documentos_forca_preditiva_seis_modelos.zip')
    args = p.parse_args()
    files = sorted(Path(args.resultados).glob('resultado_*.zip'))
    merge(args.amostra, files, args.saida, args.manifesto_original)
