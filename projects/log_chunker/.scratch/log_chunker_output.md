PS C:\_Python\_Projects\log_chunker> log-chunker analyze C:\_Python\_Projects\.dev\.rovodev\rovodev.log --reports-dir c:\_Python\_Projects\log_chunker\docs\reports
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\brsth\AppData\Local\Programs\Python\Python313\Scripts\log-chunker.exe\__main__.py", line 4, in <module>
    from log_chunker.log_chunker import main
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\log_chunker.py", line 21, in <module>
    from .chunking_engine import ChunkingEngine
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\chunking_engine.py", line 10, in <module>
    from .preprocessor import Preprocessor
ImportError: cannot import name 'Preprocessor' from 'log_chunker.preprocessor' (C:\_Python\_Projects\log_chunker\src\log_chunker\preprocessor.py). Did you mean: 'preprocessor'?
PS C:\_Python\_Projects\log_chunker> python .\log-chunker analyze C:\_Python\_Projects\.dev\.rovodev\rovodev.log --reports-dir c:\_Python\_Projects\log_chunker\docs\reports
C:\Users\brsth\AppData\Local\Programs\Python\Python313\python.exe: can't open file 'C:\\_Python\\_Projects\\log_chunker\\log-chunker': [Errno 2] No such file or directory
PS C:\_Python\_Projects\log_chunker> log-chunker.exe analyze C:\_Python\_Projects\.dev\.rovodev\rovodev.log --reports-dir c:\_Python\_Projects\log_chunker\docs\reports
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in_run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\brsth\AppData\Local\Programs\Python\Python313\Scripts\log-chunker.exe\__main__.py", line 4, in <module>
    from log_chunker.log_chunker import main
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\log_chunker.py", line 21, in <module>
    from .chunking_engine import ChunkingEngine
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\chunking_engine.py", line 10, in <module>
    from .preprocessor import Preprocessor
ImportError: cannot import name 'Preprocessor' from 'log_chunker.preprocessor' (C:\_Python\_Projects\log_chunker\src\log_chunker\preprocessor.py). Did you mean: 'preprocessor'?
PS C:\_Python\_Projects\log_chunker> python -m log_chunker analyze C:\_Python\_Projects\.dev\.rovodev\rovodev.log --reports-dir c:\_Python\_Projects\log_chunker\docs\reports
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\__main__.py", line 15, in <module>
    from log_chunker.log_chunker import main
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\log_chunker.py", line 21, in <module>
    from .chunking_engine import ChunkingEngine
  File "C:\_Python\_Projects\log_chunker\src\log_chunker\chunking_engine.py", line 10, in <module>
    from .preprocessor import Preprocessor
ImportError: cannot import name 'Preprocessor' from 'log_chunker.preprocessor' (C:\_Python\_Projects\log_chunker\src\log_chunker\preprocessor.py). Did you mean: 'preprocessor'?
PS C:\_Python\_Projects\log_chunker>
