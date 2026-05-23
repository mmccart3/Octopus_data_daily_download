from requests import get
from requests.auth import HTTPBasicAuth
from datetime import datetime,time
from sys import argv
from dotenv import load_dotenv
from mysql.connector import connect
import os

load_dotenv()
import_mpan = os.getenv("IMPORT_MPAN")
import_meter_serial_number = os.getenv("IMPORT_METER_SERIAL_NUMBER")
export_mpan = os.getenv("EXPORT_MPAN")
export_meter_serial_number = os.getenv("EXPORT_METER_SERIAL_NUMBER")
gas_meter_serial_number = os.getenv("GAS_METER_SERIAL_NUMBER")
mprn = os.getenv("MPRN")
api_key = os.getenv("API_KEY")
host = os.environ.get("HOST")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")
port = os.environ.get("PORT")
database = os.environ.get("DATABASE")

date = -2

elec_import_rate_std = 0.2112
elec_import_rate_low = 0.2112
elec_import_rate_high = 0.2816
elec_export_rate_std = 0.2112
elec_export_rate_low = 0.2112
elec_export_rate_high = 0.2816
elec_daily_standing_charge = round(0.6476,4)

gas_rate = 0.0526
gas_daily_standing_charge = round(0.3188,4)

def get_electricty_consumption():
    global api_key, date, import_mpan, import_meter_serial_number
    url = f"https://api.octopus.energy/v1/electricity-meter-points/{import_mpan}/meters/{import_meter_serial_number}/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))
    output_dict = response.json()
    readings = output_dict["results"]
    return readings

def get_electricty_export():
    global api_key, date, export_mpan, export_meter_serial_number
    url = f"https://api.octopus.energy/v1/electricity-meter-points/{export_mpan}/meters/{export_meter_serial_number}/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))
    output_dict = response.json()
    readings = output_dict["results"]
    return readings

def get_gas_consumption():
    global api_key, date, mprn, gas_meter_serial_number
    url = f"https://api.octopus.energy/v1/gas-meter-points/{mprn}/meters/{gas_meter_serial_number}/consumption/"
    response = get(url, auth=HTTPBasicAuth(api_key, ""))
    output_dict = response.json()
    readings = output_dict["results"]
    return readings

def open_database_connection():
    global host, user, password, database, port, dbconnection, mycursor
    dbconnection = connect(
        host=host,
        user=user,
        port=port,
        password=password,
        database=database
    )

    mycursor = dbconnection.cursor()

open_database_connection()

def get_list_of_current_database_readings():
    global mycursor
    sql = "SELECT interval_start FROM utility_usage_half_hour"
    mycursor.execute(sql)
    result = mycursor.fetchall()
    current_database_readings = []
    for row in result:
        current_database_readings.append(row[0].isoformat())
    return current_database_readings

electric_consumption_readings = get_electricty_consumption()
electric_export_readings = get_electricty_export()
gas_consumption_readings = get_gas_consumption()
        
list_of_current_database_readings = get_list_of_current_database_readings()
for reading in electric_consumption_readings:
    st = datetime.fromisoformat(reading['interval_start'])
    start_time = st.strftime("%Y-%m-%dT%H:%M:%S")
    print(start_time)
    start_hour = st.hour
    print(start_hour)
    if start_hour > 15 and start_hour < 19:
        elec_import_rate = elec_import_rate_high
    else:
        elec_import_rate = elec_import_rate_std       
    if start_time not in list_of_current_database_readings:
        sql = "INSERT INTO  utility_usage_half_hour (interval_start, electricity_imported_kwh, electricity_imported_rate_gbp) VALUES (%s, %s, %s)"
        val = (start_time, reading['consumption'], elec_import_rate)
        mycursor.execute(sql, val)
        print(mycursor.rowcount, "record inserted.")
        dbconnection.commit()
    else:
        update_sql = "UPDATE utility_usage_half_hour SET electricity_imported_kwh = %s, electricity_imported_rate_gbp = %s WHERE interval_start = %s"
        update_val = (reading['consumption'], elec_import_rate, start_time)
        mycursor.execute(update_sql, update_val)
        print(mycursor.rowcount, "record updated.")
        dbconnection.commit()

        
list_of_current_database_readings = get_list_of_current_database_readings()

for reading in electric_export_readings:
    st = datetime.fromisoformat(reading['interval_start'])
    start_time = st.strftime("%Y-%m-%dT%H:%M:%S")
    print(start_time)
    start_hour = st.hour
    print(start_hour)
    if start_hour > 15 and start_hour < 19:
        elec_export_rate = elec_export_rate_high
    else:
        elec_export_rate = elec_export_rate_std 
    if start_time not in list_of_current_database_readings:
        sql = "INSERT INTO  utility_usage_half_hour (interval_start, electricity_exported_kwh, electricity_exported_rate_gbp) VALUES (%s, %s, %s)"
        val = (start_time, reading['consumption'], elec_export_rate)
        mycursor.execute(sql, val)
        dbconnection.commit()
        print(mycursor.rowcount, "record inserted.")
    else:
        update_sql = "UPDATE utility_usage_half_hour SET electricity_exported_kwh = %s, electricity_exported_rate_gbp = %s WHERE interval_start = %s"
        update_val = (reading['consumption'], elec_export_rate, start_time)
        mycursor.execute(update_sql, update_val)
        dbconnection.commit()
        print(mycursor.rowcount, "record updated.") 
        
list_of_current_database_readings = get_list_of_current_database_readings()
        
for reading in gas_consumption_readings:
    st = datetime.fromisoformat(reading['interval_start'])
    start_time = st.strftime("%Y-%m-%dT%H:%M:%S")
    print(start_time)
    if start_time not in list_of_current_database_readings:
        sql = "INSERT INTO  utility_usage_half_hour (interval_start, gas_cubic_metres, gas_rate_gbp) VALUES (%s, %s, %s)"
        val = (start_time, reading['consumption'], gas_rate)
        mycursor.execute(sql, val)
        dbconnection.commit()
        print(mycursor.rowcount, "record inserted.")
    else:
        update_sql = "UPDATE utility_usage_half_hour SET gas_cubic_metres = %s, gas_rate_gbp = %s WHERE interval_start = %s"
        update_val = (reading['consumption'], gas_rate, start_time)
        mycursor.execute(update_sql, update_val)
        print(mycursor.rowcount, "record updated.")
        dbconnection.commit()


        


dbconnection.close()