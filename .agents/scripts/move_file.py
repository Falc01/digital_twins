"""
move_file.py
Script atômico para movimentação e renomeação de arquivos e pastas.
"""
import os
import shutil
import argparse
import json

def move_file(src: str, dst: str) -> dict:
    try:
        if not os.path.exists(src):
            return {"status": "error", "message": f"Origem não encontrada: {src}"}
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.move(src, dst)
        return {"status": "success", "src": src, "dst": dst}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    args = parser.parse_args()
    print(json.dumps(move_file(args.src, args.dst), indent=2))
