"""ELCA = El Camino Real de Tierra Adentro, ELTE = El Camino Real de los Tejas (NPS unit codes)."""
import json, pathlib
T = {t['ref']: t for t in json.load(open(pathlib.Path(__file__).resolve().parents[1] / '.github/scripts/kpc_us_trails.json'))}


def test_tejas_is_elte():
    assert T['US-4568']['url'].startswith('ELTE_NHT') and 'Tejas' in T['US-4568']['name']


def test_tierra_adentro_is_elca():
    assert T['US-4569']['url'].startswith('ELCA_NHT') and 'Tierra Adentro' in T['US-4569']['name']
