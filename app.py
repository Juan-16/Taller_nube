import os, time
from datetime import datetime, timezone
from bson import json_util
from flask import Flask, request, Response
from flask_cors import CORS
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)
CORS(app)
SERVICE = os.environ.get("SERVICE")  # "read" | "write"
_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=5000)
    return _client


def resp(data, code=200):
    return Response(json_util.dumps(data), status=code, mimetype="application/json")


@app.get("/health")
def health():
    return "ok"


if SERVICE == "write":
    @app.post("/items")
    def escribir():
        try:
            body = request.get_json(silent=True) or {}
            inicio = time.perf_counter()
            db = get_client()[os.environ["MONGO_DB"]]
            db["registros"].insert_one({
                "nombre": body.get("nombre", "sin_nombre"),
                "valor": int(body.get("valor", 0)),
                "fecha": datetime.now(timezone.utc).isoformat(),
            })
            ms = (time.perf_counter() - inicio) * 1000
            return resp({"motor": "mongodb", "operacion": "escritura",
                         "mensaje": "Documento insertado correctamente",
                         "tiempo_ms": round(ms, 2)})
        except Exception as e:
            return resp({"error": str(e)}, 500)

if SERVICE == "read":
    @app.get("/items")
    def leer():
        try:
            limite = int(request.args.get("limite", 10))
            inicio = time.perf_counter()
            db = get_client()[os.environ["MONGO_DB"]]
            res = list(db["registros"].find({}, {"_id": 0}).sort("_id", DESCENDING).limit(limite))
            ms = (time.perf_counter() - inicio) * 1000
            return resp({"motor": "mongodb", "operacion": "lectura",
                         "resultados": res, "tiempo_ms": round(ms, 2)})
        except Exception as e:
            return resp({"error": str(e)}, 500)
