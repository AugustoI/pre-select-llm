"""Run exactly one model; store only checkpoints/results after success."""
import gc
import importlib.metadata as md
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing
import core
from bundles import read_sample, read_result, atomic_zip, json_bytes, rows_bytes, validate_result, hash_bytes, fingerprint


def setup(sample_zip, scratch, output_dir):
    manifest, docs = read_sample(sample_zip)
    if hash_bytes(Path(core.__file__).read_bytes()) != manifest['protocol']['core_sha256']:
        raise ValueError('Notebook e amostra usam implementações diferentes.')
    scratch, output_dir = Path(scratch).resolve(), Path(output_dir).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    session = scratch / manifest['sample_id'][:16]
    session.mkdir(exist_ok=True)
    print(f'Amostra: {len(docs)} documentos | ID {manifest["sample_id"][:16]}')
    print('Temporários:', scratch)
    print('ZIPs salvos na pasta:', output_dir)
    print('Registro persistente (não exclua):', state_dir({'manifest': manifest, 'output': output_dir}))
    print(f'Espaço livre no disco de temporários: {shutil.disk_usage(scratch).free / 2**30:.1f} GiB')
    return {'manifest': manifest, 'docs': docs, 'scratch': scratch, 'session': session, 'output': output_dir}


def result_path(state, model):
    return state['output'] / ('resultado_' + model.replace('/', '__') + '_' + state['manifest']['sample_id'][:12] + '.zip')


def state_dir(state):
    folder = state['output'] / 'preselect_estado' / state['manifest']['sample_id'][:16]
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def receipt_path(state, model):
    if model not in state['manifest']['model_revisions']:
        raise ValueError('Modelo não está na suíte da amostra.')
    return state_dir(state) / (model.replace('/', '__') + '.concluido.json')


def save_receipt(path, record):
    """Publish a durable completion marker only after the output was validated."""
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'wb') as f:
        f.write(json_bytes(record))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def completed_receipt(state, model):
    path = receipt_path(state, model)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding='utf-8'))
    manifest = state['manifest']
    expected = {'status': 'complete', 'model': model, 'sample_id': manifest['sample_id'],
                'protocol_id': manifest['protocol_id'], 'revision': manifest['model_revisions'][model],
                'documents': len(state['docs']), 'core_sha256': manifest['protocol']['core_sha256']}
    if any(record.get(k) != v for k, v in expected.items()):
        raise RuntimeError(f'Registro de conclusão incompatível: {path}. Não será usado para pular o modelo.')
    if not isinstance(record.get('zip_sha256'), str) or len(record['zip_sha256']) != 64:
        raise RuntimeError('Registro de conclusão sem hash válido do ZIP.')
    return record


def mark_completed(state, model):
    destination = result_path(state, model)
    metadata, benchmark, by_id = read_result(destination, state['manifest'], state['docs'])
    record = {'status': 'complete', 'model': model, 'sample_id': metadata['sample_id'],
              'protocol_id': metadata['protocol_id'], 'revision': metadata['revision'],
              'core_sha256': metadata['core_sha256'], 'documents': len(by_id),
              'zip_name': destination.name, 'zip_sha256': core.file_hash(destination),
              'benchmark_score': benchmark['score'],
              'completed_utc': datetime.now(timezone.utc).isoformat(),
              'meaning': 'calculation completed and ZIP validated; does not assert user downloaded it'}
    save_receipt(receipt_path(state, model), record)
    return record


def ensure_local_package(state, sample_data, local_sources):
    path = state['output'] / ('unificacao_local_' + state['manifest']['sample_id'][:12] + '.zip')
    marker = state_dir(state) / 'pacote_local.json'
    signature = fingerprint({'sample_sha256': hash_bytes(sample_data), 'sources': local_sources})
    if marker.exists() and json.loads(marker.read_text(encoding='utf-8')).get('signature') == signature:
        print('Pacote de unificação local já foi gerado:', path.name,
              '(presente)' if path.exists() else '(removido da pasta; não será recriado)')
        return path
    atomic_zip(path, {'amostra_preselect.zip': sample_data,
                     **{name: source.encode('utf-8') for name, source in local_sources.items()}})
    save_receipt(marker, {'signature': signature, 'zip_name': path.name, 'zip_sha256': core.file_hash(path)})
    print('Pacote de unificação local salvo:', path)
    return path


def release_model_cache(state, model):
    """A durable receipt also permits cleanup after the user removes the ZIP."""
    if completed_receipt(state, model) is None:
        mark_completed(state, model)
    root = (state['scratch'] / 'hf' / 'hub').resolve()
    target = root / ('models--' + model.replace('/', '--'))
    if target.is_symlink():
        raise RuntimeError('Pasta de modelo é um symlink: limpeza cancelada.')
    if target.exists():
        if target.resolve().parent != root or not target.name.startswith('models--'):
            raise RuntimeError('Caminho de cache inválido.')
        shutil.rmtree(target)
        print('Cache de pesos liberado:', model)


def run_model(state, model):
    manifest, docs = state['manifest'], state['docs']
    destination = result_path(state, model)
    record = completed_receipt(state, model)
    if record is not None:
        if destination.exists() and core.file_hash(destination) != record['zip_sha256']:
            raise RuntimeError('O ZIP presente foi alterado após a conclusão: ' + str(destination))
        release_model_cache(state, model)
        print('PULANDO modelo já concluído:', model,
              '| ZIP presente' if destination.exists() else '| ZIP removido; conclusão preservada')
        return destination if destination.exists() else None
    if destination.exists():
        # Adopt complete archives produced before this receipt-based version,
        # or after an interruption between publishing the ZIP and its receipt.
        mark_completed(state, model)
        release_model_cache(state, model)
        print('Resultado anterior validado e registrado; pulando:', model)
        return destination
    import torch
    from tqdm.auto import tqdm
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from huggingface_hub import constants, HfApi
    if model not in manifest['model_revisions']:
        raise ValueError('Modelo não está na suíte da amostra.')
    hub = (state['scratch'] / 'hf' / 'hub').resolve()
    if Path(constants.HF_HUB_CACHE).resolve() != hub:
        raise RuntimeError('Cache Hugging Face aponta para outro disco. Reinicie o kernel e execute a configuração primeiro.')
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError('Este protocolo requer uma GPU CUDA com BF16.')
    for package, expected in {'transformers': '4.57.1', 'tokenizers': '0.22.1', 'lm_eval': '0.4.9.2'}.items():
        if md.version(package) != expected:
            raise RuntimeError(f'Versão incorreta de {package}; execute instalação e reinicie o kernel.')
    revision = manifest['model_revisions'][model]
    info = HfApi().model_info(model, revision=revision, files_metadata=True)
    # Conservative estimate for the largest selected weight format, plus headroom.
    safe = [f for f in info.siblings if f.rfilename.endswith('.safetensors')]
    weights = safe or [f for f in info.siblings if f.rfilename.endswith('.bin') and 'pytorch_model' in f.rfilename]
    weight_bytes = sum(f.size or 0 for f in weights)
    required = max(3 * 2**30, weight_bytes + 2 * 2**30)
    if shutil.disk_usage(state['scratch']).free < required:
        raise RuntimeError(f'Pouco espaço antes do download: reserve {required / 2**30:.1f} GiB livres no disco temporário. Nenhum cálculo foi apagado.')
    model_dir = state['session'] / model.replace('/', '__')
    model_dir.mkdir(exist_ok=True)
    bench_path = model_dir / 'benchmark.json'
    cfg = manifest['protocol']
    with closing(sqlite3.connect(model_dir / 'checkpoint.sqlite')) as db:
        db.execute('CREATE TABLE IF NOT EXISTS scores (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        db.commit()
        existing = {key: json.loads(data) for key, data in db.execute('SELECT id, data FROM scores')}
        pending = [d for d in docs if d['document_id'] not in existing]
        tokenizer = model_obj = None
        try:
            if pending or not bench_path.exists():
                print('Modelo:', model, '| documentos pendentes:', len(pending), flush=True)
                tokenizer = AutoTokenizer.from_pretrained(model, revision=revision, cache_dir=str(hub))
                model_obj = AutoModelForCausalLM.from_pretrained(model, revision=revision, cache_dir=str(hub),
                    torch_dtype=torch.bfloat16, attn_implementation='eager').to('cuda:0').eval()
                limit = getattr(model_obj.config, 'max_position_embeddings', None) or getattr(model_obj.config, 'n_positions', None)
                if limit and cfg['context'] > limit:
                    raise ValueError('Contexto maior que o suportado pelo modelo.')
                if not bench_path.exists():
                    print('Avaliando capacidade nos benchmarks completos...', flush=True)
                    core.evaluate_capability(model_obj, tokenizer, cfg, bench_path, 'cuda:0')
                for doc in tqdm(pending, desc=model):
                    row = core.score_text(model_obj, tokenizer, doc['text'], cfg['context'], cfg['stride'], 'cuda:0')
                    row.update(document_id=doc['document_id'], text_sha256=doc['text_sha256'])
                    db.execute('INSERT OR REPLACE INTO scores VALUES (?, ?)', (doc['document_id'], json.dumps(row, allow_nan=False)))
                    db.commit()
            rows = [json.loads(data) for _, data in db.execute('SELECT id, data FROM scores ORDER BY id')]
        finally:
            del tokenizer, model_obj
            gc.collect()
            torch.cuda.empty_cache()
    benchmark = core.read_json(bench_path)
    metadata = {'sample_id': manifest['sample_id'], 'protocol_id': manifest['protocol_id'],
                'model': model, 'revision': revision, 'dtype': cfg['dtype'], 'core_sha256': cfg['core_sha256'],
                'packages': {p: md.version(p) for p in ('torch', 'transformers', 'lm_eval', 'tokenizers', 'datasets')},
                'gpu': torch.cuda.get_device_name(0)}
    validate_result(manifest, docs, metadata, benchmark, rows)
    atomic_zip(destination, {'result.json': json_bytes(metadata), 'benchmark.json': json_bytes(benchmark), 'bpc.jsonl': rows_bytes(rows)})
    mark_completed(state, model)
    release_model_cache(state, model)
    print(f'ZIP salvo: {destination.name} ({destination.stat().st_size / 2**20:.2f} MiB)')
    return destination


def run_all(state):
    outputs = []
    for number, model in enumerate(state['manifest']['model_revisions'], 1):
        print(f'\n[{number}/{len(state["manifest"]["model_revisions"])}] {model}', flush=True)
        outputs.append(run_model(state, model))
    print('\nTodos os modelos têm conclusão registrada.')
    print('ZIPs disponíveis na pasta:', state['output'])
    print('Preserve esta pasta para reexecutar sem repetir:', state_dir(state))
    return outputs
