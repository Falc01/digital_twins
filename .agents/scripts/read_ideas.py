import os
import sys
import argparse
import json

GLOBAL_VAULT = r"C:\Users\joaof\.gemini\config\memory\ideasVault.md"

PROJECT_MAP = {
    "socratic_brain": r"C:\\Users\\joaof\\Documents\\projetos\\socratic_brain",
    "solana_edge_compute": r"C:\\Users\\joaof\\Documents\\projetos\\solana_edge_compute",
    "compiladores": r"C:\\Users\\joaof\\Documents\\Unifacs\\materias\\compiladores",
    "computacao_grafica": r"C:\\Users\\joaof\\Documents\\Unifacs\\materias\\computacao_grafica",
    "usoport": r"C:\\Users\\joaof\\Documents\\usoport",
    "digital_twins": r"C:\Users\joaof\Documents\Unifacs\ICs\digital_twins",
    "pci_site": r"C:\Users\joaof\Documents\Unifacs\ICs\ppdru_IC\pci_site",
    "brigadistas": r"C:\Users\joaof\Documents\projetos\brigadistas",
    "rpg_hub": r"C:\Users\joaof\Documents\projetos\rpg_hub",
    "coleta_inteligente": r"C:\Users\joaof\Documents\projetos\coleta_inteligente",
    "rpg_tarot": r"C:\Users\joaof\Documents\projetos\rpg_tarot",
    "easy_vote": r"C:\Users\joaof\Documents\projetos\easy_vote",
    "omni": r"C:\Users\joaof\Documents\projetos\omni",
    "blockchain_stuff": r"C:\Users\joaof\Documents\projetos\blockchain_stuff"
}

def read_ideas(project: str = None) -> dict:
    if project:
        p_key = project.lower().strip().replace("ideias_", "").replace("ideia_", "").replace("ideias", "").replace("ideia", "")
        if p_key in PROJECT_MAP:
            p_dir = PROJECT_MAP[p_key]
            ideas_file = os.path.join(p_dir, ".agents", "ideas.md")
            if os.path.exists(ideas_file):
                with open(ideas_file, "r", encoding="utf-8") as f:
                    return {"status": "success", "type": "project", "project": p_key, "content": f.read()}
            else:
                return {"status": "success", "type": "project", "project": p_key, "content": f"# 💡 Cofre Local de Ideias — {p_key}\n\nNenhuma ideia cadastrada ainda neste projeto."}
        else:
            return {"status": "error", "message": f"Projeto '{project}' não encontrado."}

    # If no project specified, read global + count local projects
    local_counts = {}
    for p_name, p_dir in PROJECT_MAP.items():
        ideas_file = os.path.join(p_dir, ".agents", "ideas.md")
        if os.path.exists(ideas_file):
            try:
                with open(ideas_file, "r", encoding="utf-8") as f:
                    lines = [l for l in f.readlines() if l.strip().startswith("- **")]
                    local_counts[p_name] = len(lines)
            except Exception:
                local_counts[p_name] = 0
        else:
            local_counts[p_name] = 0

    global_content = ""
    if os.path.exists(GLOBAL_VAULT):
        with open(GLOBAL_VAULT, "r", encoding="utf-8") as f:
            global_content = f.read()

    return {
        "status": "success",
        "type": "global_summary",
        "global_vault": global_content,
        "project_counts": local_counts
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None)
    args = parser.parse_args()

    print(json.dumps(read_ideas(args.project), indent=2))
