import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from verificar import verify
from unificar import merge


class DeliveryTests(unittest.TestCase):
    def test_original_results_and_consolidated_are_identical(self):
        report = verify(ROOT)
        self.assertEqual((report['documents'], report['models'], report['bpc_values']), (1000, 6, 6000))
        self.assertEqual(report['comparable_pairs_per_document'], [15])

    def test_missing_and_duplicate_result_are_rejected(self):
        inputs = sorted((ROOT / 'dados/resultados_por_modelo').glob('resultado_*.zip'))
        sample = ROOT / 'dados/amostras/amostra_preselect.zip'
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'invalid.zip'
            with self.assertRaisesRegex(ValueError, 'Faltam'):
                merge(sample, inputs[:-1], output)
            with self.assertRaisesRegex(ValueError, 'Dois ZIPs'):
                merge(sample, inputs + inputs[:1], output)
            self.assertFalse(output.exists())

    def test_gpu_notebooks_embed_the_audited_runtime(self):
        for path in (ROOT / 'notebooks').glob('PreSelect_GPU_*.ipynb'):
            notebook = json.loads(path.read_text(encoding='utf-8'))
            code = ''.join(notebook['cells'][4]['source'])
            sources = next(ast.literal_eval(node.value) for node in ast.parse(code).body
                           if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                           and node.targets[0].id == 'SOURCES')
            for name in ('core.py', 'bundles.py', 'gpu_step.py'):
                self.assertEqual(sources[name].encode('utf-8'), (ROOT / 'src' / name).read_bytes())

    def test_analysis_is_executed_and_contains_no_error_output(self):
        notebook = json.loads((ROOT / 'notebooks/01_Explorar_Documentos_e_Resultados.ipynb').read_text(encoding='utf-8'))
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertIsNotNone(cell['execution_count'])
                self.assertFalse(any(output['output_type'] == 'error' for output in cell['outputs']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
