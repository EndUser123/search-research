import os

os.environ['BASH_SYNTAX_VALIDATOR_ENABLED'] = 'true'
os.environ['BASH_SYNTAX_VALIDATOR_BLOCKING'] = 'true'

import PreToolUse_bash_syntax_validator as hook

print(f'Hook ENABLED: {hook.ENABLED}')
print(f'Hook BLOCKING: {hook.BLOCKING}')

result = hook.check_command(r'cd P:\.claude\hooks')
print(f'Validation result: {result}')
