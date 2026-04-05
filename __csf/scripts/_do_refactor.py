from pathlib import Path
import re

source_file = Path('P:/__csf/src/core/cognitive_feedback_loop_orchestrator.py')
original = source_file.read_text(encoding='utf-8')

# Add IterationResult enum after LoopState
iteration_result_enum = '''

class IterationResult(str, Enum):
    """Result of a single iteration execution.

    Used for internal control flow within the orchestrator.
    """
    CONVERGED = "converged"
    HALT_ERROR = "halt_error"
    CONTINUE = "continue"
'''

pattern = r'(    HALTED_TIMEOUT = "halted_timeout"
)'
match = re.search(pattern, original)
if match:
    step1 = original[:match.end()] + iteration_result_enum + original[match.end:]
    print('Step 1: Added IterationResult enum')
else:
    step1 = original
    print('Step 1: Skipped')

# Replace string returns with enum
step2 = step1.replace('return "converged"', 'return IterationResult.CONVERGED')
step2 = step2.replace('return "halt_error"', 'return IterationResult.HALT_ERROR') 
step2 = step2.replace('return "continue"', 'return IterationResult.CONTINUE')
print('Step 2: Replaced string returns with enum')

# Add type alias
type_alias = '
#: Type for convergence check callback function
ConvergenceCheckCallable = Callable[[dict[str, Any]], tuple[bool, float, list[str]]]
'
pattern = r'(logger = logging\.getLogger\(__name__\))'
match = re.search(pattern, step2)
if match:
    step3 = step2[:match.end()] + type_alias + step2[match.end:]
    print('Step 3: Added type alias')
else:
    step3 = step2
    print('Step 3: Skipped')

# Update parameter type
step4 = step3.replace('convergence_check: Callable[[dict[str, Any]], tuple[bool, float, list[str]]]', 'convergence_check: ConvergenceCheckCallable')
print('Step 4: Updated parameter type')

# Write result
source_file.write_text(step4, encoding='utf-8')
print('Refactoring complete!')
