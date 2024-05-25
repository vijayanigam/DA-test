
from fastapi import FastAPI
from starlette.responses import JSONResponse
from error_codes import errors
import model
import json
from datetime import datetime

import numpy as np
import pandas as pd

app = FastAPI()
files_directory = 'files'


def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    radius = 6371
    distance = radius * c
    return distance


@app.post("/report_gen", response_model=model.timeRange)
def get_all_conditions(request: model.timeRange):
    try:
        start_time = request.start_time
        end_time = request.end_time

        start_datetime = datetime.utcfromtimestamp(start_time)
        end_datetime = datetime.utcfromtimestamp(end_time)

        trip_df = pd.read_csv('files/Trip-Info.csv')
        trial_df = pd.read_parquet('files/merged_data.parquet')  # storing trail data as parquet for faster computation
        trial_df.drop(columns=['Unnamed: 0'], inplace=True)
        trip_df['date_time'] = pd.to_datetime(trip_df['date_time'], format='%Y%m%d%H%M%S')
        prc_trip_df = trip_df[(trip_df['date_time'] >= start_datetime) & (trip_df['date_time'] <= end_datetime)]

        trial_df['tis'] = pd.to_datetime(trial_df['tis'], unit='s')
        prc_trial_df = trial_df[(trial_df['tis'] >= start_datetime) & (trial_df['tis'] <= end_datetime)]

        if prc_trial_df.empty:
            return JSONResponse(status_code=errors["404"]["code"], content=errors["404"]["message"])

        # cleaning lat lon values, dropping zeros
        prc_trial_df = prc_trial_df[(prc_trial_df['lat'] != 0) | (prc_trial_df['lon'] != 0)]
        prc_trial_df = prc_trial_df[(prc_trial_df['lat'].between(-90, 90)) & (prc_trial_df['lon'].between(-180, 180))]
        prc_trial_df.sort_values(by=['lic_plate_no', 'tis'])

        # compute distance traveled using haversine formula
        prc_trial_df['distance'] = prc_trial_df.groupby('lic_plate_no').apply(lambda group: haversine_distance(group['lat'], group['lon'], group['lat'].shift(), group['lon'].shift())).reset_index(level=0, drop=True)

        opt_trial_df = prc_trial_df.groupby('lic_plate_no').agg({'distance': 'sum', 'spd': 'mean', 'osf': 'sum'}).reset_index()
        opt_trip_df = prc_trip_df.groupby('vehicle_number').agg({'trip_id': 'nunique', 'transporter_name': 'first'}).reset_index()

        file_path = f'files/asset_report_{start_time}_{end_time}.xlsx'
        vehicle_asset_report = pd.merge(opt_trial_df, opt_trip_df, left_on='lic_plate_no', right_on='vehicle_number', how='inner')
        vehicle_asset_report.drop(columns=['vehicle_number'], inplace=True)
        vehicle_asset_report['trip_id'].fillna(0).astype(int).reset_index(drop=True)
        vehicle_asset_report.columns = ['License plate number', 'Distance', 'Average Speed', 'Number of Speed Violations', 'Number of Trips Completed', 'Transporter Name']
        vehicle_asset_report.to_excel(file_path, index=False)

        return JSONResponse(status_code=200, content=json.dumps({'file_path': file_path}))

    except Exception as e:
        return JSONResponse(status_code=errors["500"]["code"], content=errors["500"]["message"])
