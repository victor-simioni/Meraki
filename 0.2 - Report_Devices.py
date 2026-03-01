import os
import time
import meraki
import pandas as pd
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
from dateutil import parser  

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
EXPORT_PATH = os.path.join(BASE_DIR, "exports")
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
# FUNÇÃO SEGURA PARA CONVERTER DATA (CORRIGIDA)
# ==============================
def safe_parse_date(date_string):
    if not date_string:
        return None
    try:
        # 🔥 REMOVE " UTC" que estava causando None
        cleaned = str(date_string).replace(" UTC", "").strip()
        dt = parser.parse(cleaned)
        return dt.replace(tzinfo=None)
    except Exception as e:
        print(f"Erro ao converter data: {date_string} -> {e}")
        return None

# ==============================
# COLETAR ORGANIZAÇÕES
# ==============================
orgs = dashboard.organizations.getOrganizations(total_pages="all")

all_models_set = set()
rows = []

for org in orgs:

    org_id = org["id"]
    org_name = org["name"]

    print(f"Processando organização: {org_name}")

    row = defaultdict(int)
    row["Organization"] = org_name
    row["Networks"] = 0
    row["Devices_ALL"] = 0
    row["License_Model"] = ""
    row["License_Start"] = datetime.now().strftime("%Y-%m-%d")
    row["License_Finish"] = ""
    row["Remaining_Days"] = ""

    try:
        # Tentamos per-device
        try:
            licenses = dashboard.organizations.getOrganizationLicenses(
                org_id,
                total_pages="all"
            )

            if licenses and len(licenses) > 0:
                row["License_Model"] = "per-device"

                expiration_dates = [
                    lic.get("expirationDate")
                    for lic in licenses
                    if lic.get("expirationDate")
                ]

                if expiration_dates:
                    row["License_Finish"] = max(expiration_dates)

            else:
                row["License_Model"] = "per-device"
                row["License_Finish"] = ""

        except Exception as per_device_error:

            if "does not support per-device licensing" in str(per_device_error):
                overview = dashboard.organizations.getOrganizationLicensesOverview(org_id)
                row["License_Model"] = "co-term"
                row["License_Finish"] = overview.get("expirationDate", "")
            else:
                raise per_device_error

        # ==========================
        # CALCULAR REMAINING DAYS
        # ==========================
        start_date_obj = safe_parse_date(row["License_Start"])
        #print(f"License_Start: {start_date_obj}")

        finish_date_obj = safe_parse_date(row["License_Finish"])
        #print(f"License_Finish: {finish_date_obj}")

        if start_date_obj and finish_date_obj:
            remaining = (finish_date_obj - start_date_obj).days
            row["Remaining_Days"] = remaining
        else:
            row["Remaining_Days"] = ""

    except Exception as e:
        print(f"Erro license {org_name}: {e}")
        row["License_Model"] = "error"
        row["License_Finish"] = ""
        row["Remaining_Days"] = ""

    # ==========================
    # DEVICES
    # ==========================
    try:
        devices = dashboard.organizations.getOrganizationDevices(
            org_id,
            total_pages="all"
        )

        row["Devices_ALL"] = len(devices)

        for device in devices:
            model = device.get("model")
            if model:
                row[model] += 1
                all_models_set.add(model)

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
        row["Networks"] = 0

    rows.append(row)
    time.sleep(0.2)

# ==============================
# DATAFRAME FINAL
# ==============================
all_models = sorted(list(all_models_set))

columns = [
    "Organization",
    "Networks",
    "Devices_ALL",
    "License_Model",
    "License_Start",
    "License_Finish",
    "Remaining_Days"
] + all_models

df = pd.DataFrame(rows)

for col in columns:
    if col not in df.columns:
        df[col] = 0

df = df[columns]

# ==============================
# EXPORTAR EXCEL
# ==============================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
export_file = os.path.join(
    EXPORT_PATH,
    f"Report_Devices_{timestamp}.xlsx"
)

df.to_excel(export_file, index=False)

print("\nRelatório gerado com sucesso:")
print(export_file)
