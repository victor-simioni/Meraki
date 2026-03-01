Meraki Data Collection Automation

Automated data collection solution for the Meraki environment using Python and the Meraki Dashboard API.
This project centralizes network data extraction and transforms raw Meraki information into structured 
reports and insights — simplifying monitoring, analytics, and integration with BI tools.

🚀 Overview
This repository contains Python scripts to automate the querying and retrieval 
of data from the Cisco Meraki Dashboard API. 
The scripts fetch information about devices, networks, organizations, and more,
enabling structured analysis and simplified operational workflows.

--------------------------------------------------------------------------
🧠 Features

📡 API Integration: Connects securely to the Meraki Dashboard REST API
🔐 Secure Authentication: Uses API Key for authorized access
🗃️ Data Collection: Fetches key data such as devices, networks, and org info
📊 Modular Scripts: Each script focuses on specific data reporting tasks
🛠️ Structured Output: Data ready for use in dashboards or analytics workflows

--------------------------------------------------------------------------
📁 Included Scripts
Script	Description
0.1 - Report_Evolution_Month.py	Monthly evolution reporting of selected metrics
0.2 - Report_Devices.py	Devices inventory and status report
0.3 - Report_Backup_Orgs.py	Backup report of organizational structures
requirements.txt	Project dependencies

⚠️ The .env file is included in the repo for sample/config purposes but should 
not contain real credentials — always use secure environment variables.


⚙️ Prerequisites
Before running the project, ensure you have:
Python 3.7+
Valid Cisco Meraki API Key
Access to the Meraki Dashboard with API enabled

___________________________________________________________________________________
🔧 Installation
- Clone the repository:
git clone https://github.com/victor-simioni/Meraki.git
cd Meraki

- Create a virtual environment (optional but recommended):
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

Install dependencies:
pip install -r requirements.txt

🪪 Configuration
Create a .env file in the root of the project (or set your environment variables directly) 
with the following:

MERAKI_API_KEY=your_api_key_here

Do not commit your API key into source control. Keep it secure.

🚀 Running the Scripts
Execute each script individually depending on the report you wish to generate.

Example:
python "0.2 - Report_Devices.py"
Each script will connect to the Meraki Dashboard API and output structured data 
— either to the console or to files (depending on the script logic).

📦 Dependencies
The project uses the libraries listed in requirements.txt, such as:

requests — HTTP client for API calls
pandas — Data manipulation and transformation

Install all dependencies automatically via:
pip install -r requirements.txt

Optional predictive modeling using collected data

📄 License
This project is open source and available under the MIT License.
___________________________________________________________________________________

🚀 About
Project by Victor Simioni — Python developer focusing on data automation, analytics and network integrations.
LinkedIn: https://www.linkedin.com/in/victorsimioni/
