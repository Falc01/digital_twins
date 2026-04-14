import re
from flask import Flask, jsonify, request, send_from_directory, abort
from config import PASTA_DADOS
from table_manager import TableManager, TableNotFoundError, TableAlreadyExistsError
from dyntable import DynType
from qgis_bridge.launcher import launch_qgis

app = Flask(__name__, static_folder="web_interface", static_url_path="")
mgr = TableManager(PASTA_DADOS)

INVALID_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')


def validate_name(name: str, field: str = "nome") -> None:
    if not name or INVALID_NAME_RE.search(name):
        abort(400, description=f"{field} inválido. Não use / \" < > : | ? * ou caracteres de controle.")


def json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def load_table(name: str):
    validate_name(name, "Nome da tabela")
    try:
        return mgr.get(name)
    except TableNotFoundError as exc:
        abort(404, description=str(exc))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/styles.css")
def styles():
    return send_from_directory(app.static_folder, "styles.css")


@app.route("/app.js")
def app_js():
    return send_from_directory(app.static_folder, "app.js")


@app.route("/api/types")
def types():
    return jsonify([t.name for t in DynType])


@app.route("/api/tables", methods=["GET"])
def list_tables():
    tables = mgr.list_tables()
    return jsonify({"tables": tables})


@app.route("/api/tables", methods=["POST"])
def create_table():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    validate_name(name)
    try:
        mgr.create(name)
        return jsonify({"table": name}), 201
    except TableAlreadyExistsError as exc:
        return json_error(str(exc), 409)


@app.route("/api/tables/<string:name>", methods=["GET"])
def get_table(name):
    table = load_table(name)
    return jsonify({
        "name": table.name,
        "columns": [{
            "name": col.name,
            "type": col.dtype.name,
            "nullable": col.nullable,
            "locked": col.locked,
        } for col in table.columns],
        "row_count": table.row_count,
        "col_count": table.col_count,
    })


@app.route("/api/tables/<string:name>", methods=["DELETE"])
def delete_table(name):
    validate_name(name)
    try:
        mgr.delete(name)
        return jsonify({"deleted": name})
    except TableNotFoundError as exc:
        return json_error(str(exc), 404)


@app.route("/api/tables/<string:name>/columns", methods=["POST"])
def add_column(name):
    table = load_table(name)
    data = request.get_json(silent=True) or {}
    col_name = (data.get("name") or "").strip()
    dtype_name = (data.get("type") or "AUTO").strip().upper()
    nullable = bool(data.get("nullable", True))

    validate_name(col_name, "Nome da coluna")
    if dtype_name not in DynType.__members__:
        return json_error(f"Tipo desconhecido: {dtype_name}")

    try:
        table.add_column(col_name, DynType[dtype_name], nullable)
        mgr.save(table)
        return jsonify({"column": col_name}), 201
    except Exception as exc:
        return json_error(str(exc), 400)


@app.route("/api/tables/<string:name>/columns/<string:col_name>", methods=["DELETE"])
def delete_column(name, col_name):
    table = load_table(name)
    if not col_name:
        return json_error("Nome da coluna é obrigatório.")
    try:
        table.remove_column(col_name)
        mgr.save(table)
        return jsonify({"deleted": col_name})
    except Exception as exc:
        return json_error(str(exc), 400)


@app.route("/api/tables/<string:name>/columns/<string:col_name>/rename", methods=["POST"])
def rename_column(name, col_name):
    table = load_table(name)
    data = request.get_json(silent=True) or {}
    new_name = (data.get("new_name") or "").strip()
    validate_name(new_name, "Novo nome da coluna")
    try:
        table.rename_column(col_name, new_name)
        mgr.save(table)
        return jsonify({"renamed": {"old": col_name, "new": new_name}})
    except Exception as exc:
        return json_error(str(exc), 400)


@app.route("/api/launch_qgis", methods=["POST"])
def launch_qgis_route():
    try:
        launch_qgis()
        return jsonify({"message": "QGIS launched"})
    except Exception as exc:
        return json_error(str(exc), 500)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": getattr(error, "description", str(error))}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": getattr(error, "description", str(error))}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Erro interno no servidor."}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8502, debug=True)
