"""Interfaz CLI de la Mesa de Ayuda IA - Departamento Legal, Patito S.A.

Uso:
    python main.py

Escribe preguntas en lenguaje natural. El orquestador decide que agente(s) especializado(s)
deben responder y consolida la respuesta final. Escribe 'salir' para terminar.
"""
from src.orquestador import preguntar


def main() -> None:
    print("=" * 70)
    print("  Mesa de Ayuda IA - Departamento Legal - Patito S.A.")
    print("  (Prototipo - Semillero de Inteligencia Artificial)")
    print("=" * 70)
    print("\nEscribe tu pregunta legal (o 'salir' para terminar).")
    print("Las respuestas son orientativas y no sustituyen la asesoria de un abogado.\n")

    historial: list = []  # memoria de la conversacion (imprescindible para flujos de
                           # confirmacion de varios turnos, ej. el agente de accion)

    while True:
        try:
            pregunta = input(">>> Tu pregunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo...")
            break

        if pregunta.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        if pregunta.lower() in {"reiniciar", "nueva conversacion"}:
            historial = []
            print("Historial reiniciado.\n")
            continue
        if not pregunta:
            continue

        try:
            resultado = preguntar(pregunta, historial=historial)
        except Exception as e:
            print(f"\n[ERROR] No se pudo procesar la consulta: {type(e).__name__}: {e}\n")
            continue

        historial = resultado["historial"]

        print(f"\n>>> Respuesta:\n{resultado['respuesta']}\n")
        participantes = ", ".join(resultado["agentes_participantes"]) or "ninguno"
        print(f">>> Agentes participantes: {participantes}")
        if resultado["fuentes"]:
            print(">>> Fuentes consultadas (trazabilidad):")
            for agente, lista_fuentes in resultado["fuentes"].items():
                print(f"    - {agente}: {len(lista_fuentes)} fragmento(s) recuperado(s)")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
