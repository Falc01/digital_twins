from __future__ import annotations

import os
import sys
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger("qgis_server_tester")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configurações do servidor a serem testadas (prioriza variáveis do Docker/Ambiente)
QGIS_SERVER_URL = os.getenv("QGIS_SERVER_URL", "http://localhost:8010")
# Caminho interno do projeto QGIS no container
QGIS_PROJECT_PATH_CONTAINER = os.getenv("QGIS_PROJECT_PATH", "/infra/dados/projeto_iot.qgz")


def run_http_request(url: str, params: dict) -> tuple[int, bytes, str | None]:
    """
    Executa uma chamada HTTP GET simples e retorna (status_code, body, content_type).
    Usa urllib para não exigir dependência externa de 'requests'.
    """
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    logger.info("Executando chamada: %s", full_url)
    
    try:
        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            body = response.read()
            content_type = response.headers.get("Content-Type")
            return status, body, content_type
    except urllib.error.HTTPError as e:
        logger.error("Erro HTTP %d ao acessar %s: %s", e.code, full_url, e.reason)
        try:
            return e.code, e.read(), e.headers.get("Content-Type")
        except Exception:
            return e.code, b"", None
    except Exception as e:
        logger.error("Erro de conexão ao acessar %s: %s", full_url, e)
        return 500, b"", None


def test_wms_capabilities() -> None:
    """
    Testa se o QGIS Server responde ao GetCapabilities do WMS.
    """
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetCapabilities",
        "MAP": QGIS_PROJECT_PATH_CONTAINER
    }
    
    status, body, content_type = run_http_request(QGIS_SERVER_URL, params)
    
    assert status == 200, f"Expected HTTP 200, got {status}"
    assert b"<WMS_Capabilities" in body, f"Response is not valid WMS Capabilities XML. Response: {body[:300].decode('utf-8', errors='ignore')}"
    logger.info("[OK] WMS GetCapabilities respondeu corretamente.")


def test_wms_getmap() -> None:
    """
    Testa a renderização de mapas do WMS (GetMap) retornando uma imagem PNG.
    """
    layer_name = os.getenv("TEST_LAYER", "sensor_readings_demo")
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layer_name,
        "CRS": "EPSG:4326",
        "BBOX": "-90,-180,90,180",  # Extensão global para garantir cobertura
        "WIDTH": "256",
        "HEIGHT": "256",
        "FORMAT": "image/png",
        "MAP": QGIS_PROJECT_PATH_CONTAINER
    }
    
    status, body, content_type = run_http_request(QGIS_SERVER_URL, params)
    
    assert status == 200, f"WMS GetMap falhou. Status: {status}. Response: {body[:300].decode('utf-8', errors='ignore')}"
    assert content_type == "image/png", f"Expected Content-Type image/png, got {content_type}"
    assert body.startswith(b"\x89PNG"), "Response body is not a valid PNG image"
    logger.info("[OK] WMS GetMap renderizou a camada '%s' com sucesso.", layer_name)


def test_wfs_getfeature() -> None:
    """
    Testa a exportação de feições vetoriais do WFS (GetFeature) em formato GeoJSON.
    """
    layer_name = os.getenv("TEST_LAYER", "sensor_readings_demo")
    # O QGIS Server substitui espaços por underscores ao exportar TypeNames de WFS.
    typename = layer_name.replace(" ", "_")
    
    params = {
        "SERVICE": "WFS",
        "VERSION": "1.1.0",
        "REQUEST": "GetFeature",
        "TYPENAME": typename,
        "OUTPUTFORMAT": "application/json",
        "MAP": QGIS_PROJECT_PATH_CONTAINER
    }
    
    status, body, content_type = run_http_request(QGIS_SERVER_URL, params)
    
    assert status == 200, f"WFS GetFeature falhou. Status: {status}. Response: {body[:300].decode('utf-8', errors='ignore')}"
    assert "json" in str(content_type).lower(), f"Expected JSON Content-Type, got {content_type}"
    
    try:
        data = json.loads(body.decode("utf-8"))
        features_count = len(data.get("features", []))
        logger.info(
            "[OK] WFS GetFeature respondeu com sucesso para a camada '%s' (%d feições detectadas).",
            typename, features_count
        )
    except json.JSONDecodeError:
        raise AssertionError("WFS respondeu HTTP 200, mas o corpo não continha um JSON válido.")


def main():
    logger.info("=== Iniciando Teste de Integração do QGIS Server ===")
    logger.info("Servidor Alvo: %s", QGIS_SERVER_URL)
    logger.info("Projeto no Container: %s", QGIS_PROJECT_PATH_CONTAINER)
    
    try:
        test_wms_capabilities()
        test_wms_getmap()
        test_wfs_getfeature()
        logger.info("=== TODOS OS TESTES PASSARAM COM SUCESSO ===")
        sys.exit(0)
    except AssertionError as e:
        logger.error("=== HOUVE FALHAS NO TESTE DE INTEGRAÇÃO DO QGIS SERVER: %s ===", e)
        sys.exit(1)
    except Exception as e:
        logger.error("=== ERRO INESPERADO: %s ===", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
