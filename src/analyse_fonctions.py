import os
import ast

def list_python_files(root_dir):
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # Ignore virtual env and cache
        if "__pycache__" in dirpath or "venv" in dirpath:
            continue
        for f in filenames:
            if f.endswith('.py') and f != os.path.basename(__file__):
                py_files.append(os.path.join(dirpath, f))
    return py_files

def extract_functions(file_path):
    with open(file_path, encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=file_path)
    return [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]

def find_usages(file_path, function_names):
    usages = set()
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        for fname in function_names:
            # Avoid counting the definition itself
            if content.count(fname + '(') > 1:
                usages.add(fname)
    return usages

def main(src_dir):
    py_files = list_python_files(src_dir)
    all_functions = {}
    for file in py_files:
        funcs = extract_functions(file)
        if funcs:
            all_functions[file] = funcs

    used_functions = set()
    for file in py_files:
        for fname in sum(all_functions.values(), []):
            if fname in find_usages(file, [fname]):
                used_functions.add(fname)

    print("Fonctions inutilisées :")
    for file, funcs in all_functions.items():
        for f in funcs:
            if f not in used_functions and not f.startswith("__"):
                print(f"- {f} (définie dans {file})")

if __name__ == "__main__":
    main(".")  # "." pour scanner le dossier courant
