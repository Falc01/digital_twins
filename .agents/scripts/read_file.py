"""
read_file.py
Script atômico para leitura de arquivos em múltiplos formatos.
"""
import os
import argparse
import json

def read_file(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"Arquivo não encontrado: {path}"}
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"status": "success", "path": path, "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    print(json.dumps(read_file(args.path), indent=2))
