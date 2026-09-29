import os
import json
import glob

CONFIG_DIR = r"C:\Users\joaof\.gemini\config"
DOWNLOADS_DIR = r"C:\Users\joaof\Downloads"

IGNORE_SYSTEM_FILES = {"desktop.ini", "thumbs.db", ".ds_store"}

def run_home_diagnostics():
    skills_count = len([f for f in glob.glob(os.path.join(CONFIG_DIR, "skills", "*.md")) if not f.endswith("SKILL.md")])
    scripts_count = len(glob.glob(os.path.join(CONFIG_DIR, "scripts", "*.py")))
    commands_count = len(glob.glob(os.path.join(CONFIG_DIR, "commands", "*.md")))
    hooks_count = len(glob.glob(os.path.join(CONFIG_DIR, "hooks", "*.py")))
    rules_count = len(glob.glob(os.path.join(CONFIG_DIR, "rules", "*.md")))

    hired_status = []
    known_paths = [
        ("usoport", r"C:\Users\joaof\Documents\usoport"),
        ("compiladores", r"C:\Users\joaof\Documents\Unifacs\materias\compiladores"),
        ("computacao_grafica", r"C:\Users\joaof\Documents\Unifacs\materias\computacao_grafica"),
        ("digital_twins", r"C:\Users\joaof\Documents\Unifacs\ICs\digital_twins"),
        ("pci_site", r"C:\Users\joaof\Documents\Unifacs\ICs\ppdru_IC\pci_site"),
        ("brigadistas", r"C:\Users\joaof\Documents\projetos\brigadistas"),
        ("rpg_hub", r"C:\Users\joaof\Documents\projetos\rpg_hub"),
        ("coleta_inteligente", r"C:\Users\joaof\Documents\projetos\coleta_inteligente"),
        ("rpg_tarot", r"C:\Users\joaof\Documents\projetos\rpg_tarot"),
        ("solana_edge_compute", r"C:\Users\joaof\Documents\projetos\solana_edge_compute"),
        ("socratic_brain", r"C:\Users\joaof\Documents\projetos\socratic_brain")
    ]

    for name, path in known_paths:
        sup_file = os.path.join(path, ".agents", "SUPERVISOR.md")
        act_file = os.path.join(path, ".agents", "memory", "activeContext.md")
        if os.path.exists(sup_file):
            status_text = "Em operação"
            if os.path.exists(act_file):
                try:
                    with open(act_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        for line in content.splitlines():
                            if "Estado Atual" in line:
                                status_text = line.split(":", 1)[-1].strip()
                                break
                except Exception:
                    pass

            # Detect modern (v2.0) vs legacy (v1.0)
            is_modern = False
            try:
                with open(sup_file, "r", encoding="utf-8") as sf:
                    sup_content = sf.read()
                    if 'version: "2.0' in sup_content or "v2.0" in sup_content:
                        is_modern = True
            except Exception:
                pass

            if not is_modern:
                compaction_rule = os.path.join(path, ".agents", "rules", "atlas.memory.compaction.rule.md")
                if os.path.exists(compaction_rule):
                    is_modern = True

            version_text = "v2.0 (Atual)" if is_modern else "v1.0 (Legada)"
            badge = "🟢" if is_modern else "🟡"

            hired_status.append({
                "name": name,
                "path": path,
                "badge": badge,
                "version": version_text,
                "is_modern": is_modern,
                "status": status_text
            })

    pending_projects = ["easy_vote", "omni", "blockchain_stuff"]

    downloads_files = []
    if os.path.exists(DOWNLOADS_DIR):
        downloads_files = [
            f for f in os.listdir(DOWNLOADS_DIR)
            if not f.startswith(".") 
            and f.lower() not in IGNORE_SYSTEM_FILES
            and os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]

    vault_file = os.path.join(CONFIG_DIR, "memory", "ideasVault.md")
    ideas_summary = "Cofre ativo"
    if os.path.exists(vault_file):
        try:
            with open(vault_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip().startswith("- **")]
                ideas_summary = f"{len(lines)} ideias cadastradas"
        except Exception:
            pass

    return {
        "status": "success",
        "ecosystem": {
            "rules": rules_count,
            "skills": skills_count,
            "scripts": scripts_count,
            "commands": commands_count,
            "hooks": hooks_count
        },
        "hired_supervisors": hired_status,
        "pending_projects": pending_projects,
        "downloads_inbox": {
            "total_files": len(downloads_files),
            "recent_files": downloads_files[:5]
        },
        "ideas_summary": ideas_summary
    }

if __name__ == "__main__":
    print(json.dumps(run_home_diagnostics(), indent=2))
