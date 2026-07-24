"""Script reproducible para (re)generar los 3 indices vectoriales, uno por agente de lectura.

Uso:
    python build_indexes.py

Cada corrida es idempotente: si el indice ya existe en vectorstores/<nombre>/, se reutiliza (no
se vuelve a llamar a la API de embeddings). Para forzar una regeneracion completa, borra la
carpeta vectorstores/ antes de correr este script.
"""
from src.config import DATA_DIR
from src.vectorstore_utils import construir_o_cargar_vectorstore

INDICES = {
    "contratos": DATA_DIR / "01_Clausulas_Contractuales.txt",
    "proteccion_datos": DATA_DIR / "02_Proteccion_Datos.txt",
    "cumplimiento": DATA_DIR / "03_Cumplimiento_Etica.txt",
}

if __name__ == "__main__":
    for nombre, ruta in INDICES.items():
        print(f"Generando/cargando indice '{nombre}' desde {ruta} ...")
        construir_o_cargar_vectorstore(str(ruta), nombre)
    print("\nListo. Indices disponibles en ./vectorstores/")
