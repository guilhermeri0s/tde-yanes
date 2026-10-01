import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request

API_KEY = "AIzaSyCOC1v63jSD0nChUSNnLNa5Qvw9TQUZzpk"
DATABASE_URL = "https://painel-reposicao-default-rtdb.firebaseio.com"
DEVICE_EMAIL = "balanca@reposicao.app"
DEVICE_PASSWORD = "SENHA_DO_DISPOSITIVO"


def http(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        sys.exit(f"Erro HTTP {e.code} em {url.split('?')[0]}: {e.read().decode()}")


def login():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    res = http("POST", url, {"email": DEVICE_EMAIL, "password": DEVICE_PASSWORD, "returnSecureToken": True})
    return res["idToken"], time.time() + int(res["expiresIn"]) - 60


def send_weight(token, shelf_id, weight_kg):
    url = f"{DATABASE_URL}/shelves/{shelf_id}.json?auth={token}"
    return http("PATCH", url, {"currentWeightKg": round(weight_kg, 3), "updatedAt": {".sv": "timestamp"}})


def main():
    p = argparse.ArgumentParser(description="Simula a balança enviando o peso de uma prateleira para o Firebase.")
    p.add_argument("shelf_id", help="ID da prateleira (aparece no Firebase em /shelves)")
    p.add_argument("--peso", type=float, help="Envia um único peso em kg e encerra")
    p.add_argument("--unidade", type=float, default=1.03, help="Peso de 1 unidade em kg (modo automático)")
    p.add_argument("--capacidade", type=int, default=20, help="Capacidade da prateleira (modo automático)")
    p.add_argument("--intervalo", type=float, default=3, help="Segundos entre leituras (modo automático)")
    args = p.parse_args()

    token, expires = login()
    print("Dispositivo autenticado.")

    if args.peso is not None:
        send_weight(token, args.shelf_id, args.peso)
        print(f"Peso enviado: {args.peso:.3f} kg")
        return

    units = args.capacidade
    while True:
        if time.time() > expires:
            token, expires = login()
        if units <= 0:
            units = args.capacidade
            print("Prateleira reabastecida.")
        else:
            units -= random.choice([0, 1, 1, 2])
            units = max(units, 0)
        weight = units * args.unidade + random.uniform(-0.005, 0.005)
        if random.random() < 0.1 and units > 0:
            weight += args.unidade * 0.4
            print("(simulando produto estranho)")
        send_weight(token, args.shelf_id, max(weight, 0))
        print(f"{units:>3} un  ->  {weight:.3f} kg")
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
