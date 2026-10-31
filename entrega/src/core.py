import hashlib, json, math, os, random
from pathlib import Path
from urllib.parse import urlparse

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def save_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    os.replace(tmp, path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def original_sources(n, seed):
    """Exactly the 1,000 candidate paths enumerated by the original download.py."""
    candidates = []
    for g in range(1, 11):
        for local in range(10):
            indices = random.Random(g * 10 + local).sample(range(1, 3000), 2999)
            for i in indices[100:110]:
                candidates.append(
                    'https://data.commoncrawl.org/contrib/datacomp/DCLM-refinedweb/'
                    f'global-shard_{g:02d}_of_10/local-shard_{local}_of_10/'
                    f'shard_{i:08d}_processed.jsonl.zstd')
    if not 1 <= n <= len(candidates):
        raise ValueError('source_shards deve estar entre 1 e 1000.')
    return random.Random(seed).sample(candidates, n)

def normalize_document(row, url, line):
    text = row.get('text')
    if not isinstance(text, str) or not text.strip():
        return None
    metadata = row.get('metadata') or {}
    if not isinstance(metadata, dict):
        metadata = {}
    warc = row.get('warcinfo') or row.get('warc') or {}
    if not isinstance(warc, dict):
        warc = {}
    address = row.get('url') or metadata.get('url') or row.get('WARC-Target-URI') or warc.get('WARC-Target-URI') or ''
    # DCLM pools may store WARC headers in metadata.
    address = address or metadata.get('WARC-Target-URI', '')
    domain = urlparse(address).hostname or ''
    if not domain:
        return None
    return {'document_id': digest([url, line]), 'original_id': row.get('id'), 'text': text,
            'url': address, 'domain': domain.lower(), 'n_chars': len(text),
            'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'source_url': url, 'source_line': line}

def windows(n_tokens, context, stride):
    """Indices refer to [BOS] + text tokens; every text token is a target once."""
    if context < 1 or not 1 <= stride <= context:
        raise ValueError('Janela/passo inválidos.')
    first_target = 1
    while first_target <= n_tokens:
        last_target = min(n_tokens + 1, context + 1 if first_target == 1 else first_target + stride)
        begin = max(0, last_target - 1 - context)
        yield begin, last_target - 1, first_target, last_target
        first_target = last_target

def score_token_ids(model, ids, bos, context, stride, device):
    import torch
    import torch.nn.functional as F
    sequence = [bos] + list(ids)
    total, count = 0.0, 0
    with torch.inference_mode():
        for begin, input_end, target_begin, target_end in windows(len(ids), context, stride):
            inputs = torch.tensor([sequence[begin:input_end]], dtype=torch.long, device=device)
            logits = model(input_ids=inputs, use_cache=False).logits[0]
            start = target_begin - 1 - begin
            n = target_end - target_begin
            targets = torch.tensor(sequence[target_begin:target_end], dtype=torch.long, device=device)
            losses = F.cross_entropy(logits[start:start+n].float(), targets, reduction='none')
            if not torch.isfinite(losses).all():
                raise ValueError('Perda não finita.')
            total += losses.double().sum().item()
            count += n
            del inputs, logits, losses, targets
    if count != len(ids):
        raise RuntimeError('Cobertura de tokens incompleta.')
    return total, count

def score_text(model, tokenizer, text, context, stride, device):
    if not text:
        raise ValueError('Documento vazio.')
    ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    if not ids:
        raise ValueError('Documento sem tokens.')
    bos = tokenizer.bos_token_id
    if bos is None:
        bos = tokenizer.eos_token_id
    if bos is None:
        raise ValueError('Tokenizer sem BOS/EOS para predizer o primeiro token.')
    loss, count = score_token_ids(model, ids, bos, context, stride, device)
    return {'bpc': loss / (len(text) * math.log(2)), 'nll_sum': loss, 'n_tokens': len(ids),
            'n_scored_tokens': count, 'n_chars': len(text), 'prefix_token_id': bos}

def evaluate_capability(model, tokenizer, cfg, destination, device):
    from lm_eval import simple_evaluate
    from lm_eval.models.huggingface import HFLM
    lm = HFLM(pretrained=model, tokenizer=tokenizer, batch_size=1, max_length=cfg['context'],
              device=device, softmax_dtype='float32')
    results = simple_evaluate(model=lm, tasks=list(cfg['benchmarks']), num_fewshot=0,
                              limit=cfg['benchmark_limit'], log_samples=False, bootstrap_iters=0,
                              random_seed=cfg['seed'], numpy_random_seed=cfg['seed'],
                              torch_random_seed=cfg['seed'], fewshot_random_seed=cfg['seed'])
    per_task = {task: float(results['results'][task][metric]) for task, metric in cfg['benchmarks'].items()}
    report = {'score': sum(per_task.values()) / len(per_task), 'per_task': per_task,
              'raw_results': results['results'], 'versions': results.get('versions'),
              'n_samples': results.get('n-samples'), 'configs': results.get('configs'),
              'git_hash': results.get('git_hash'), 'limit': cfg['benchmark_limit']}
    # Task configurations can contain callables; persist their representations too.
    report = json.loads(json.dumps(report, default=str))
    save_json(destination, report)
    del lm, results
    return report
