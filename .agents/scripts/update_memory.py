"""
update_memory.py
Script atômico para atualização de seções em arquivos de memória viva (.md).
"""
import os
import argparse
import json

def update_memory(file_path: str, section: str, text: str) -> dict:
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Arquivo de memória não encontrado: {file_path}"}
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        entry = f"- {text}\n"
        if section in content:
            new_content = content.replace(section, section + "\n" + entry)
        else:
            new_content = content + f"\n\n{section}\n{entry}"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return {"status": "success", "file": file_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--section", required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    print(json.dumps(update_memory(args.file, args.section, args.text), indent=2))
