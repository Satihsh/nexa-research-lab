"""Minimal test runner (no pytest needed): python run_tests.py test_x.py [...] runs every test_* function."""
import importlib.util
import sys
import traceback

fails = total = 0
for path in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location(path[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in sorted(n for n in dir(mod) if n.startswith('test_')):
        total += 1
        try:
            getattr(mod, name)()
            print('PASS', path, name)
        except Exception:
            fails += 1
            print('FAIL', path, name)
            traceback.print_exc()
print(f'{total - fails}/{total} passed')
sys.exit(1 if fails else 0)
