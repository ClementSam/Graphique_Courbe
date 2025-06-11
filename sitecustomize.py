import importlib.util, sys, pathlib
pkg_path = pathlib.Path(__file__).resolve().parent / 'io'
if pkg_path.exists():
    spec = importlib.util.spec_from_file_location('io', pkg_path / '__init__.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.__path__ = [str(pkg_path)]
    sys.modules['io'] = module
