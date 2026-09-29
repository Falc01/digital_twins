import os
import sys
import argparse
import json
from datetime import datetime

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

def save_idea(text: str, project: str = None, category: int = 3) -> dict:
    date_str = datetime.now().strftime("%d/%m/%Y")
    target_project = project.lower().strip() if project else None

    # Auto-detect project from text if not explicitly provided
    if not target_project:
        text_lower = text.lower()
        for p_key in PROJECT_MAP.keys():
            if p_key in text_lower or p_key.replace("_", "") in text_lower or p_key.replace("_", " ") in text_lower:
                target_project = p_key
                break

    # If targeting a project
    if target_project and target_project in PROJECT_MAP:
        p_dir = PROJECT_MAP[target_project]
        ideas_file = os.path.join(p_dir, ".agents", "ideas.md")
        os.makedirs(os.path.dirname(ideas_file), exist_ok=True)
        
        entry = f"- **{date_str}**: {text}\n"
        
        if not os.path.exists(ideas_file):
            content = f"# 💡 Cofre Local de Ideias — {target_project}\n\n## 📌 Ideias Pendentes & Features\n\n{entry}"
        else:
            with open(ideas_file, "r", encoding="utf-8") as f:
                content = f.read()
            if "## 📌 Ideias Pendentes & Features" in content:
                content = content.replace("## 📌 Ideias Pendentes & Features\n", f"## 📌 Ideias Pendentes & Features\n{entry}")
            else:
                content += f"\n{entry}"
                
        with open(ideas_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"status": "success", "scope": "local", "project": target_project, "file": ideas_file, "entry": text}

    # Else target global vault
    entry = f"- **{date_str}**: {text}\n"
    with open(GLOBAL_VAULT, "r", encoding="utf-8") as f:
        content = f.read()

    category_markers = {
        1: "## 🎯 1. Ideias para Projetos Ativos\n",
        2: "## 🤖 2. Ideias & Módulos para o OMNI\n",
        3: "## 🚀 3. Ideias Incubadas para Projetos Novos\n"
    }

    marker = category_markers.get(category, category_markers[3])

    if marker in content:
        new_content = content.replace(marker, marker + entry)
    else:
        new_content = content + f"\n\n{marker}\n{entry}"

    with open(GLOBAL_VAULT, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {"status": "success", "scope": "global", "vault_path": GLOBAL_VAULT, "entry": text}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--category", type=int, default=3)
    args = parser.parse_args()

    print(json.dumps(save_idea(args.text, args.project, args.category), indent=2))
