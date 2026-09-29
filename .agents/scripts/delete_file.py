"""
delete_file.py
Script atômico para remoção segura de arquivos ou diretórios.
"""
import os
import shutil
import argparse
import json

def delete_file(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"Caminho não encontrado: {path}"}
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        return {"status": "success", "deleted": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    print(json.dumps(delete_file(args.path), indent=2))
