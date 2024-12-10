import matplotlib
matplotlib.use('Agg')
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import os


def make_images(input_file, location_name, start_date, end_date, output_dir="static/forecast_images"):
    """
    Generate and save forecast graphs for WVHT and WTMP for a given location within a specified date range.

    Parameters:
    - input_file: Path to the input CSV file.
    - location_name: Name of the location (used in the filenames).
    - start_date: Start date of the prediction range (YYYY-MM-DD).
    - end_date: End date of the prediction range (YYYY-MM-DD).
    - output_dir: Directory to save the output images.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Output file names
    output_image_wvht = os.path.join(output_dir, f"{location_name}_wvht_forecast.png")
    output_image_wtmp = os.path.join(output_dir, f"{location_name}_wtmp_forecast.png")

    # Load and preprocess data
    df = pd.read_csv(input_file)
    df['Year'] = df['#YY'].astype(int)
    df['Month'] = df['MM'].astype(int)
    df['Day'] = df['DD'].astype(int)
    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day']])

    # Check necessary columns
    if 'WVHT' not in df.columns or 'WTMP' not in df.columns:
        raise ValueError(f"Missing WVHT or WTMP column in {location_name}.")

    # Prepare dataframes for Prophet
    df_wvht = df.rename(columns={'datetime': 'ds', 'WVHT': 'y'})[['ds', 'y', 'WTMP']]
    df_wtmp = df.rename(columns={'datetime': 'ds', 'WTMP': 'y'})[['ds', 'y']]

    # Convert start_date and end_date to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter training data
    train_wvht = df_wvht[df_wvht['ds'] < start_date]
    train_wtmp = df_wtmp[df_wtmp['ds'] < start_date]

    # Drop rows where WTMP is 999 in WTMP training data only
    train_wtmp = train_wtmp[train_wtmp['y'] != 999]

    if train_wvht.empty or train_wtmp.empty:
        raise ValueError(f"Insufficient data for training for {location_name}.")

    # Forecast WTMP
    wtmp_model = Prophet(yearly_seasonality=True, interval_width=0.90)
    wtmp_model.fit(train_wtmp)

    # Generate future WTMP predictions for the specified date range
    future_wtmp = wtmp_model.make_future_dataframe(
        periods=(end_date - train_wtmp['ds'].max()).days
    )
    wtmp_forecast = wtmp_model.predict(future_wtmp)

    # Filter WTMP predictions for the exact user-specified range
    wtmp_forecast = wtmp_forecast[(wtmp_forecast['ds'] >= start_date) & (wtmp_forecast['ds'] <= end_date)]

    # Forecast WVHT
    wvht_model = Prophet(yearly_seasonality=True, interval_width=0.70)
    wvht_model.add_regressor('WTMP')
    train_wvht_for_fit = train_wvht.dropna(subset=['y', 'WTMP'])
    wvht_model.fit(train_wvht_for_fit)

    # Generate future WVHT predictions for the specified date range
    future_wvht = pd.DataFrame({'ds': pd.date_range(start=start_date, end=end_date)})
    future_wvht = future_wvht.merge(wtmp_forecast[['ds', 'yhat']].rename(columns={'yhat': 'WTMP'}),
                                     on='ds', how='left')
    wvht_forecast = wvht_model.predict(future_wvht)

    # Filter WVHT predictions for the exact user-specified range
    wvht_forecast = wvht_forecast[(wvht_forecast['ds'] >= start_date) & (wvht_forecast['ds'] <= end_date)]

    # Generate WVHT plot for the specified date range
    plt.figure(figsize=(10, 6))
    plt.plot(wvht_forecast['ds'], wvht_forecast['yhat'], label='Predicted WVHT', marker='o')
    plt.fill_between(wvht_forecast['ds'], wvht_forecast['yhat_lower'], wvht_forecast['yhat_upper'], alpha=0.2,
                     label='Confidence Interval')
    plt.title(f'WVHT Forecast for {location_name} ({start_date.date()} to {end_date.date()})')
    plt.xlabel('Date')
    plt.ylabel('WVHT')
    plt.legend()
    plt.grid()
    plt.savefig(output_image_wvht)
    plt.close()

    # Generate WTMP plot for the specified date range
    plt.figure(figsize=(10, 6))
    plt.plot(wtmp_forecast['ds'], wtmp_forecast['yhat'], label='Predicted WTMP', marker='o', color='red')
    plt.fill_between(wtmp_forecast['ds'], wtmp_forecast['yhat_lower'], wtmp_forecast['yhat_upper'], alpha=0.2,
                     color='red', label='Confidence Interval')
    plt.title(f'WTMP Forecast for {location_name} ({start_date.date()} to {end_date.date()})')
    plt.xlabel('Date')
    plt.ylabel('WTMP')
    plt.legend()
    plt.grid()
    plt.savefig(output_image_wtmp)
    plt.close()

    return output_image_wvht, output_image_wtmp