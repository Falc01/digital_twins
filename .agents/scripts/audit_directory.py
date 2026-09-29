"""
audit_directory.py
Script atômico para inspeção e auditoria de diretórios.
"""
import os
import argparse
import json

def audit_directory(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"Diretório não encontrado: {path}"}
        files = []
        dirs = []
        for item in os.listdir(path):
            fp = os.path.join(path, item)
            if os.path.isfile(fp):
                files.append({"name": item, "size_bytes": os.path.getsize(fp)})
            elif os.path.isdir(fp):
                dirs.append({"name": item})
        return {"status": "success", "path": path, "total_files": len(files), "total_dirs": len(dirs), "files": files, "directories": dirs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    print(json.dumps(audit_directory(args.path), indent=2))
