import zipfile
import xml.etree.ElementTree as ET
import os
import argparse
import sys

def enable_wfs_for_project(qgz_path: str) -> bool:
    if not os.path.exists(qgz_path):
        print(f"[enable_wfs] Projeto não encontrado: {qgz_path}")
        return False

    qgs_temp = "projeto_iot_temp.qgs"
    styles_db = "ajbMfp_styles.db"
    
    # 1. Extrair
    try:
        with zipfile.ZipFile(qgz_path, "r") as z:
            # Extrai apenas o arquivo .qgs
            qgs_name = [name for name in z.namelist() if name.endswith(".qgs")][0]
            z.extract(qgs_name, ".")
            os.rename(qgs_name, qgs_temp)
            # Extrai o styles.db se existir
            if styles_db in z.namelist():
                z.extract(styles_db, ".")
    except Exception as e:
        print(f"[enable_wfs] Erro ao extrair projeto .qgz: {e}")
        return False

    # 2. Ler XML e injetar propriedades WFS
    try:
        tree = ET.parse(qgs_temp)
        root = tree.getroot()
        
        properties = root.find(".//properties")
        if properties is not None:
            # Remove qualquer configuração anterior de WFSLayers/WFSTLayers
            for child in list(properties):
                if child.tag in ["WFSLayers", "WFSTLayers"]:
                    properties.remove(child)
            
            # Encontra os IDs de todas as camadas vetoriais válidas no projeto
            layer_ids = []
            for l in root.findall('.//maplayer'):
                if l.get('type') == 'vector':
                    layer_id_node = l.find('id')
                    layer_name_node = l.find('layername')
                    if layer_id_node is not None and layer_name_node is not None:
                        layer_ids.append(layer_id_node.text)
                        print(f"[enable_wfs] Habilitando WFS para: '{layer_name_node.text}'")
            
            if layer_ids:
                # Injeta a lista de IDs no WFSLayers
                wfs_layers = ET.SubElement(properties, "WFSLayers", {"type": "QStringList"})
                for lid in layer_ids:
                    val = ET.SubElement(wfs_layers, "value")
                    val.text = lid
                print(f"[enable_wfs] Configuração WFS injetada para {len(layer_ids)} camadas.")
            else:
                print("[enable_wfs] Nenhuma camada vetorial encontrada no XML do projeto.")
        else:
            print("[enable_wfs] Erro: seção de propriedades do projeto QGIS não encontrada.")
            return False

        # Salva o XML modificado
        tree.write(qgs_temp, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        print(f"[enable_wfs] Erro ao processar XML do QGS: {e}")
        return False

    # 3. Re-compactar o projeto .qgz
    try:
        with zipfile.ZipFile(qgz_path, "w") as z:
            z.write(qgs_temp, os.path.basename(qgz_path).replace(".qgz", ".qgs"))
            if os.path.exists(styles_db):
                z.write(styles_db)
    except Exception as e:
        print(f"[enable_wfs] Erro ao re-compactar arquivo .qgz: {e}")
        return False
    finally:
        # Limpa temporários
        if os.path.exists(qgs_temp):
            os.remove(qgs_temp)
        if os.path.exists(styles_db):
            os.remove(styles_db)

    print("[enable_wfs] Processamento WFS finalizado com sucesso.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Injetor de WFS Headless para projetos QGIS")
    parser.add_argument("--project", required=True, help="Caminho do arquivo do projeto QGIS (.qgz)")
    args = parser.parse_args()
    
    success = enable_wfs_for_project(args.project)
    sys.exit(0 if success else 1)
