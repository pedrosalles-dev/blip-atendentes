"""
Relatório de Atendentes - Blip Desk API
Busca todos os atendentes de múltiplos bots e consolida num único CSV.

Para adicionar mais bots: inclua um novo item na lista BOTS.
"""

import requests
import uuid
import csv
import os
from datetime import datetime

# ── Bots ───────────────────────────────────────────────────────────────────────
BOTS = [
    {"name": "Bot 14",        "contract_id": "captaaibuilder14",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxNDphNks0ZnpmUzRmU3lKR0kwUktsRQ=="},
    {"name": "Quinto Andar",  "contract_id": "quintoandarcaptaai", "key": "Key cXVpbnRvYW5kYXJjYXB0YWFpOmNsbXZnaUd1eWxjN1dTS3pES0pS"},
    {"name": "Bot 1",         "contract_id": "captaiath1",         "key": "Key Y2FwdGFpYXRoMTo5c2RPNFZZZzduZWV5WHNzdk9oQw=="},
    {"name": "Bot 2",         "contract_id": "captaiath2",         "key": "Key Y2FwdGFpYXRoMjpaZmM3ajVhRHJRUUtsQ1luS3ZpWQ=="},
    {"name": "Bot 3",         "contract_id": "captaiath3",         "key": "Key Y2FwdGFpYXRoMzpWRExxOW51WGNIbFZwUXN4cnU4VA=="},
    {"name": "Bot 4",         "contract_id": "captaiath4",         "key": "Key Y2FwdGFpYXRoNDpkZEhmSUVDSWZKZHBCTzlzR2U0RA=="},
    {"name": "Bot 5",         "contract_id": "captaiath5",         "key": "Key Y2FwdGFpYXRoNTpjSjFwQlBhclNMRmhReFp1d252Sw=="},
    {"name": "Bot 6",         "contract_id": "captaiath6",         "key": "Key Y2FwdGFpYXRoNjpKQ0xJMERWOHBGR095Nld0VVMwZQ=="},
    {"name": "Bot 8",         "contract_id": "captaiath8",         "key": "Key Y2FwdGFpYXRoODpVQVp3aDJMRE54VHFRV2V2MW9Maw=="},
    {"name": "Bot 9",         "contract_id": "captaaibuilder9",    "key": "Key Y2FwdGFhaWJ1aWxkZXI5OmtGc0JEaXFwUUpUZXhmQ1lRUElX"},
    {"name": "Bot 10",        "contract_id": "captaaibuilder10",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxMDpjWVFOUVEwcHF1QThoQ2hzeUZpUg=="},
    {"name": "Bot 11",        "contract_id": "captaaibuilder11",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxMTpWZTN0T1JQdk15dFJhR2xJTGIzeA=="},
    {"name": "Bot 15",        "contract_id": "captaaibuilder15",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxNTo2cFNGcWROdU5FR01hTU9nYndVOA=="},
    {"name": "Bot 16",        "contract_id": "captaaibuilder16",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxNjo1U0hGcmVGMWQ3OXgxaVUwa0trMA=="},
    {"name": "Bot 17",        "contract_id": "captaaibuilder17",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxNzpUNm41NUIwYlQ1aG5paU5qRUNzRA=="},
    {"name": "Bot 18",        "contract_id": "captaaibuilder18",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxODp4YWRrMnRVeXpYMUxSU1VmYkFLSA=="},
    {"name": "Bot 19",        "contract_id": "captaaibuilder19",   "key": "Key Y2FwdGFhaWJ1aWxkZXIxOTpFSDRNeHkyU0ROYWdKZ3ZIUno4RQ=="},
]

# ── Configurações ──────────────────────────────────────────────────────────────
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "atendentes.csv")
PAGE_SIZE   = 100

AGENT_FIELDS = [
    "run_date",
    "run_hour",
    "bot",
    "identity",
    "fullName",
    "email",
    "teams",
    "status",
    "lastServiceDate",
    "agentSlots",
    "ticketsInService",
]

# ──────────────────────────────────────────────────────────────────────────────

def fix_full_name(agent: dict) -> dict:
    """
    Se fullName parecer um e-mail, converte para nome legível.
    Ex: sandra.barbosa@quintoandar.com → Sandra Barbosa
    """
    name = agent.get("fullName", "")
    if "@" in name:
        name_part = name.split("@")[0]          # sandra.barbosa
        agent["fullName"] = " ".join(
            part.capitalize() for part in name_part.split(".")
        )                                        # Sandra Barbosa
    else:
        agent["fullName"] = name.title()        # LEILIANE GONÇALVES → Leiliane Gonçalves
    return agent


def send_command(contract_id: str, key: str, payload: dict) -> dict:
    url     = f"https://{contract_id}.http.msging.net/commands"
    headers = {"Authorization": key, "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def get_agents(contract_id: str, key: str) -> list:
    agents = []
    skip   = 0
    while True:
        payload = {
            "id":     str(uuid.uuid4()),
            "to":     "postmaster@desk.msging.net",
            "method": "get",
            "uri":    f"/agents?$skip={skip}&$take={PAGE_SIZE}",
        }
        data = send_command(contract_id, key, payload)

        if data.get("status") != "success":
            raise RuntimeError(f"Erro da API: {data.get('reason', data)}")

        resource = data.get("resource", {})
        items    = resource.get("items", [])
        total    = resource.get("total", len(items))

        agents.extend(items)
        skip += len(items)

        if not items or skip >= total:
            break

    return agents


def export_csv(rows: list, run_date: str, run_hour: str) -> None:
    if not rows:
        print("Nenhum atendente encontrado.")
        return

    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AGENT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row["run_date"] = run_date
            row["run_hour"] = run_hour
            writer.writerow(row)

    print(f"✓ {len(rows)} registros exportados para '{OUTPUT_PATH}'")


if __name__ == "__main__":
    now      = datetime.now()
    run_date = now.strftime("%d-%m-%Y")
    run_hour = now.strftime("%H:%M")

    all_rows = []
    for bot in BOTS:
        print(f"Buscando atendentes — {bot['name']} ...")
        try:
            agents = get_agents(bot["contract_id"], bot["key"])
            for agent in agents:
                agent["bot"] = bot["name"]
                fix_full_name(agent)
            all_rows.extend(agents)
            print(f"  ✓ {len(agents)} atendentes encontrados")
        except Exception as e:
            print(f"  ✗ Erro: {e}")

    print(f"\nTotal geral: {len(all_rows)} atendentes em {len(BOTS)} bots")
    export_csv(all_rows, run_date, run_hour)
