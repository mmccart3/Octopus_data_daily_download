from requests import get
from requests.auth import HTTPBasicAuth
from datetime import datetime
from sys import argv
from dotenv import load_dotenv
import os

load_dotenv()
import_mpan = os.getenv("IMPORT_MPAN")
print(import_mpan)
export_mpan = os.getenv("EXPORT_MPAN")
mprn = os.getenv("MPRN")
api_key = os.getenv("API_KEY")

date = -2

def elec_import(mpan):
    global api_key, date
    # print("enetering elec_export")

    url = "https://api.octopus.energy/v1/electricity-meter-points/"+mpan+"/meters/22J0393023/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))

    output_dict = response.json()

    total_elec_cost_yesterday = 0
    total_elec_consumption_yesterday = 0
    elec_rate_std = 0.2112
    elec_rate_low = 0.2112
    elec_rate_high = 0.2816

    standing_charge = round(0.6476,4)

    for readings in (output_dict["results"]):
        reading_day = datetime.fromisoformat(readings["interval_start"]).day
        reading_hour = datetime.fromisoformat(readings["interval_start"]).hour
        if  reading_day == datetime.now().day + date:
            if (reading_hour < 2) or (reading_hour >= 5 and reading_hour < 16) or (reading_hour >= 19):
                total_elec_cost_yesterday += (float(readings["consumption"]) * elec_rate_std)
                total_elec_consumption_yesterday += float(readings["consumption"])
            elif (reading_hour >= 2 and reading_hour < 5):
                total_elec_cost_yesterday += (float(readings["consumption"]) * elec_rate_low)
                total_elec_consumption_yesterday += float(readings["consumption"])
            else:
                total_elec_cost_yesterday += (float(readings["consumption"]) * elec_rate_high)
                total_elec_consumption_yesterday += float(readings["consumption"])
    yesterdays_variable_cost = round(total_elec_cost_yesterday,2)
    yesterday_full_cost = round(total_elec_cost_yesterday + standing_charge,2)  
    print(f"Imported {total_elec_consumption_yesterday}kwh cost £{yesterdays_variable_cost} + standing charge of £{standing_charge} = £{yesterday_full_cost}")
    return yesterday_full_cost


def elec_export(mpan):
    global api_key, date
    # print("enetering elec_export")
    url = "https://api.octopus.energy/v1/electricity-meter-points/"+mpan+"/meters/22J0393023/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))

    output_dict = response.json()

    total_elec_cost_yesterday = 0
    total_elec_consumption_yesterday = 0
    elec_rate_std = 0.2112
    elec_rate_low = 0.2112
    elec_rate_high = 0.2816

    standing_charge = round(0,4)

    for readings in (output_dict["results"]):
        reading_day = datetime.fromisoformat(readings["interval_start"]).day
        reading_hour = datetime.fromisoformat(readings["interval_start"]).hour
        elec_used = float(readings["consumption"])
        if  reading_day == datetime.now().day + date:
            if (reading_hour < 2) or (reading_hour >= 5 and reading_hour < 16) or (reading_hour >= 19):
                total_elec_cost_yesterday += (elec_used * elec_rate_std)
                total_elec_consumption_yesterday += elec_used
            elif (reading_hour >= 2 and reading_hour < 5):
                total_elec_cost_yesterday += (elec_used * elec_rate_low)
                total_elec_consumption_yesterday += elec_used
            else:
                total_elec_cost_yesterday += (elec_used * elec_rate_high)
                total_elec_consumption_yesterday += elec_used
    yesterdays_variable_cost = round(total_elec_cost_yesterday,2)
    yesterday_full_cost = round(total_elec_cost_yesterday + standing_charge,2)
    total_elec_consumption_yesterday = round(total_elec_consumption_yesterday,4) 
    print(f"Exported {total_elec_consumption_yesterday}kwh value £{yesterdays_variable_cost}")
    return yesterday_full_cost

def gas_import(mprn):
    global api_key, date
    # print("enetering elec_export")
    url = "https://api.octopus.energy/v1/gas-meter-points/"+mprn+"/meters/E6P82048902200/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))

    output_dict = response.json()

    total_gas_cost_yesterday = 0
    total_gas_consumption_yesterday = 0
    gas_rate_std = 0.0526
    
    standing_charge = round(0.3188,4)

    for readings in (output_dict["results"]):
        reading_day = datetime.fromisoformat(readings["interval_start"]).day
        gas_used = float(readings["consumption"])
        if  reading_day == datetime.now().day + date:
            total_gas_cost_yesterday += (gas_used * gas_rate_std)
            total_gas_consumption_yesterday += gas_used
        yesterdays_variable_cost = round(total_gas_cost_yesterday,2)
    yesterday_full_cost = round(total_gas_cost_yesterday + standing_charge,2)
    total_gas_consumption_yesterday = round(total_gas_consumption_yesterday,4) 
    print(f"Imported Gas {total_gas_consumption_yesterday}kwh value £{yesterdays_variable_cost} + standing charge of £{standing_charge}")
    return yesterday_full_cost

yesterday_elec_total =  round(elec_export(export_mpan) - elec_import(import_mpan),2)
print(f"Total Elec Profit/Loss yesterday = £{yesterday_elec_total}")

yesterday_gas_total = round(gas_import(mprn),2)
print(f"Gas Total = £{yesterday_gas_total}")

yesteday_total = round(yesterday_elec_total - yesterday_gas_total,2)

if yesteday_total > 0:
    print(f"Total profit yesterday = £{yesteday_total}")
else:
    print(f"Total cost yesterday = £{yesteday_total}")