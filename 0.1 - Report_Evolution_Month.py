import os
import time
import meraki
import pandas as pd
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

# ==============================
# LOAD API KEY
# ==============================
load_dotenv()
API_KEY = os.getenv("MERAKI_API_KEY")

if not API_KEY:
    raise ValueError("API Key não encontrada no arquivo .env")

# ==============================
# CONFIG EXPORT
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_PATH = os.path.join(BASE_DIR, "evolution")
os.makedirs(EXPORT_PATH, exist_ok=True)

# ==============================
# CONEXÃO MERAKI
# ==============================
dashboard = meraki.DashboardAPI(
    api_key=API_KEY,
    suppress_logging=True,
    wait_on_rate_limit=True
)

# ==============================
# COLETAR ORGANIZAÇÕES
# ==============================
orgs = dashboard.organizations.getOrganizations(total_pages="all")

rows = []

for org in orgs:

    org_id = org["id"]
    org_name = org["name"]

    print(f"Processando organização: {org_name}")

    row = defaultdict(int)
    row["Organization"] = org_name
    row["Networks"] = 0
    row["Devices_ALL"] = 0

    # ==========================
    # DEVICES
    # ==========================
    try:
        devices = dashboard.organizations.getOrganizationDevices(
            org_id,
            total_pages="all"
        )
        row["Devices_ALL"] = len(devices)
    except Exception as e:
        print(f"Erro devices {org_name}: {e}")

    # ==========================
    # NETWORKS
    # ==========================
    try:
        networks = dashboard.organizations.getOrganizationNetworks(
            org_id,
            total_pages="all"
        )
        row["Networks"] = len(networks)
    except Exception as e:
        print(f"Erro networks {org_name}: {e}")

    rows.append(row)
    time.sleep(0.2)

# ==============================
# DATAFRAME SNAPSHOT
# ==============================
df = pd.DataFrame(rows)

# Data da extração (simulando License_Start como snapshot mensal)
snapshot_date = datetime.now().strftime("%Y-%m-%d")
df["extraction_date"] = snapshot_date

# ==============================
# HISTÓRICO ACUMULADO
# ==============================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
history_file = os.path.join(EXPORT_PATH, f"Report_Evolution_Month_{timestamp}.xlsx")

if os.path.exists(history_file):
    old_df = pd.read_excel(history_file)
    df = pd.concat([old_df, df], ignore_index=True)

df.to_excel(history_file, index=False)

print("\nRelatório de crescimento mensal atualizado com sucesso:")
print(history_file)
