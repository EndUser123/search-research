import json
from pathlib import Path

config_path = Path('P:/__csf/src/config/system_config.json')

with open(config_path) as f:
    config = json.load(f)

config['paths']['csf_nip_src'] = 'P:\\__csf\\src'
config['paths']['registry_path'] = 'P:\\__csf\\src\\lib\\registry'
config['paths']['evidence_path'] = 'P:\\__csf\\src\\modules\\evidence'
config['logging']['file_path'] = 'P:\\__csf\\logs\\csf_nip.log'

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('Updated system_config.json')
