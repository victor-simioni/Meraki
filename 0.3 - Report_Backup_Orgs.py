import os
import re
import time
import requests
from datetime import datetime
from openpyxl import Workbook
from dotenv import load_dotenv

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

API_KEY = os.getenv("MERAKI_API_KEY")

if not API_KEY:
    raise ValueError("❌ MERAKI_API_KEY não encontrada no .env")

BASE_URL = "https://api.meraki.com/api/v1"

HEADERS = {
    "X-Cisco-Meraki-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# ==============================
# DIRETÓRIO EXPORT
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

EXPORT_PATH = os.path.join(
    BASE_DIR,
    "Backup",
    f"backup_{timestamp}"
)

os.makedirs(EXPORT_PATH, exist_ok=True)


# ===============================
# SAFE FILENAME
# ===============================
def safe_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:100]


# ===============================
# REQUEST HANDLER
# ===============================
def meraki_get(url):
    results = []

    while url:
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"⏳ Rate limit hit. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        if response.status_code == 404:
            print(f"⚠️ Endpoint not available: {url}")
            return []

        if response.status_code >= 400:
            print(f"❌ Error {response.status_code} at {url}")
            print(response.text)
            return []

        data = response.json()

        if isinstance(data, list):
            results.extend(data)
        else:
            return data

        link = response.headers.get("Link")
        if link and 'rel="next"' in link:
            url = link.split(";")[0].strip("<>")
        else:
            url = None

    return results


# ===============================
# EXCEL HELPER
# ===============================
def write_sheet(wb, name, data):
    ws = wb.create_sheet(title=name[:31])

    if not data:
        ws.append(["No Data"])
        return

    if isinstance(data, dict):
        data = [data]

    headers = list(data[0].keys())
    ws.append(headers)

    for row in data:
        ws.append([str(row.get(h, "")) for h in headers])


# ===============================
# MAIN FLOW
# ===============================
def collect_meraki_data():
    print("🔎 Collecting Organizations...\n")

    orgs = meraki_get(f"{BASE_URL}/organizations")

    if not orgs:
        print("❌ No organizations found.")
        return

    for org in orgs:
        org_id = org.get("id")
        org_name_raw = org.get("name", "Unknown")
        org_name = safe_filename(org_name_raw)

        print(f"\n🚀 Processing Organization: {org_name}")

        wb = Workbook()
        wb.remove(wb.active)

        # Organization detail
        org_detail = meraki_get(f"{BASE_URL}/organizations/{org_id}")

        licensing_model = None
        if isinstance(org_detail, dict):
            licensing_model = org_detail.get("licensing", {}).get("model")

        print(f"🔐 Licensing Model: {licensing_model}")

        # Licensing overview
        licensing_overview = []
        if licensing_model:
            licensing_overview = meraki_get(
                f"{BASE_URL}/organizations/{org_id}/licensing/overview"
            )
            if not licensing_overview:
                licensing_overview = {"info": "Overview not supported"}

        # Licenses / Subscriptions
        licenses = []
        subscriptions = []

        if licensing_model == "co-term":
            licenses = meraki_get(
                f"{BASE_URL}/organizations/{org_id}/licenses"
            )

        elif licensing_model == "per-device":
            subscriptions = meraki_get(
                f"{BASE_URL}/organizations/{org_id}/licensing/subscriptions"
            )

        # Devices
        devices = meraki_get(
            f"{BASE_URL}/organizations/{org_id}/devices"
        )

        # Inventory
        inventory_devices = meraki_get(
            f"{BASE_URL}/organizations/{org_id}/inventory/devices"
        )

        # Networks
        networks = meraki_get(
            f"{BASE_URL}/organizations/{org_id}/networks"
        )

        # ===============================
        # COMPLIANCE BY PRODUCT TYPE
        # ===============================
        device_count_by_type = {}

        for d in devices:
            if d.get("status") != "dormant":
                ptype = d.get("productType", "unknown")
                device_count_by_type[ptype] = device_count_by_type.get(ptype, 0) + 1

        license_count_by_type = {}

        if licensing_model == "co-term":
            for lic in licenses:
                if lic.get("status") == "active":
                    ptype = lic.get("productType", "unknown")
                    count = int(lic.get("licenseCount", 0))
                    license_count_by_type[ptype] = license_count_by_type.get(ptype, 0) + count

        elif licensing_model == "per-device":
            for sub in subscriptions:
                if sub.get("status") == "active":
                    ptype = sub.get("productType", "unknown")
                    license_count_by_type[ptype] = license_count_by_type.get(ptype, 0) + 1

        compliance_by_product = []

        all_types = set(device_count_by_type.keys()) | set(license_count_by_type.keys())

        for ptype in all_types:
            device_count = device_count_by_type.get(ptype, 0)
            license_limit = license_count_by_type.get(ptype, 0)
            compliant = device_count <= license_limit

            compliance_by_product.append({
                "productType": ptype,
                "device_count": device_count,
                "license_limit": license_limit,
                "compliant": compliant,
                "difference": license_limit - device_count
            })

        total_devices = sum(device_count_by_type.values())
        total_licenses = sum(license_count_by_type.values())

        compliance_summary = [{
            "organization": org_name_raw,
            "licensing_model": licensing_model,
            "total_devices": total_devices,
            "total_license_limit": total_licenses,
            "overall_compliant": total_devices <= total_licenses,
            "generated_at": datetime.now().isoformat()
        }]

        # ===============================
        # WRITE EXCEL
        # ===============================
        write_sheet(wb, "Organizations", orgs)
        write_sheet(wb, "Organization_Detail", org_detail)
        write_sheet(wb, "Licensing_Overview", licensing_overview)
        write_sheet(wb, "Licenses", licenses)
        write_sheet(wb, "Subscriptions", subscriptions)
        write_sheet(wb, "Devices", devices)
        write_sheet(wb, "Inventory_Devices", inventory_devices)
        write_sheet(wb, "Networks", networks)
        write_sheet(wb, "Compliance_By_Product", compliance_by_product)
        write_sheet(wb, "Compliance_Summary", compliance_summary)

        filename = os.path.join(
            EXPORT_PATH,
            f"meraki_audit_{org_name}.xlsx"
        )

        wb.save(filename)
        print(f"✅ Exported: {filename}")

    print("\n🎯 Collection Finished Successfully.")


# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    collect_meraki_data()
