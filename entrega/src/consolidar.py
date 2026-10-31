"""Rebuild consolidated results from the six archived model outputs; CPU only."""
import zipfile
from unificar import merge
from verificar import ROOT, verify
from bundles import json_bytes


def main():
    folder = ROOT / 'dados/consolidado'
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / 'documentos_forca_preditiva_seis_modelos.zip'
    merge(ROOT / 'dados/amostras/amostra_preselect.zip',
          sorted((ROOT / 'dados/resultados_por_modelo').glob('resultado_*.zip')), destination,
          ROOT / 'dados/amostras/manifesto_quatro_originais.json')
    with zipfile.ZipFile(destination) as archive:
        for name in archive.namelist():
            target = (folder / name).resolve()
            if target.parent != folder.resolve():
                raise ValueError('Caminho inesperado no consolidado.')
            target.write_bytes(archive.read(name))
    (ROOT / 'docs/verificacao.json').write_bytes(json_bytes(verify()))


if __name__ == '__main__':
    main()
