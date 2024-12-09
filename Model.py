import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import glob
import os
# Create a directory for the plots if it doesn't exist
plots_dir = 'plots'
os.makedirs(plots_dir, exist_ok=True)

# Get all CSV files in the CleanedData folder
station_files = glob.glob('CleanedData/*.csv')

output_file = 'forecast.csv'
first_run = True  # To handle header writing in the output CSV

for file_path in station_files:
    # Extract station_id from filename
    station_id = os.path.splitext(os.path.basename(file_path))[0]
    
    # Load and preprocess data
    df = pd.read_csv(file_path)
    df['Year'] = df['#YY'].astype(int)
    df['Month'] = df['MM'].astype(int)
    df['Day'] = df['DD'].astype(int)
    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day']])

    # Check necessary columns
    if 'WVHT' not in df.columns or 'WTMP' not in df.columns:
        print(f"Skipping {station_id}: Missing WVHT or WTMP column.")
        continue

    # Prepare dataframes for Prophet
    df_wvht = df.rename(columns={'datetime': 'ds', 'WVHT': 'y'})[['ds', 'y', 'WTMP']]
    df_wtmp = df.rename(columns={'datetime': 'ds', 'WTMP': 'y'})[['ds', 'y']]
    
    # Define training and testing periods
    train_cutoff = '2024-01-01'
    test_start = '2023-01-01'
    
    # Split data for WVHT
    train_wvht = df_wvht[df_wvht['ds'] < train_cutoff]
    test_wvht = df_wvht[df_wvht['ds'] >= test_start]
    
    # Split data for WTMP
    train_wtmp = df_wtmp[df_wtmp['ds'] < train_cutoff]
    test_wtmp = df_wtmp[df_wtmp['ds'] >= test_start]

    # Drop rows where WTMP is 999 in WTMP training data only
    train_wtmp = train_wtmp[train_wtmp['y'] != 999]
    if train_wvht.empty or test_wvht.empty or train_wtmp.empty or test_wtmp.empty:
        print(f"Skipping {station_id}: Insufficient data for training or testing.")
        continue
    
    # ------------------------------------
    # Step 1: Forecast WTMP First
    # ------------------------------------
    wtmp_model = Prophet(yearly_seasonality=True, interval_width=0.90)
    wtmp_model.fit(train_wtmp)
    
    last_train_date_wtmp = train_wtmp['ds'].max()
    last_test_date_wtmp = test_wtmp['ds'].max()
    periods_wtmp = (last_test_date_wtmp - last_train_date_wtmp).days

    future_wtmp = wtmp_model.make_future_dataframe(periods=periods_wtmp)
    wtmp_forecast = wtmp_model.predict(future_wtmp)
    
    # Extract WTMP predictions for the test period
    wtmp_forecast_test = wtmp_forecast[wtmp_forecast['ds'] >= test_start].copy()
    # Rename columns for clarity
    wtmp_forecast_test.rename(columns={
        'yhat': 'WTMP_pred', 
        'yhat_lower': 'WTMP_pred_lower', 
        'yhat_upper': 'WTMP_pred_upper'
    }, inplace=True)

    # ------------------------------------
    # Step 2: Use predicted WTMP as a regressor for WVHT
    # ------------------------------------
    last_train_date_wvht = train_wvht['ds'].max()
    last_test_date_wvht = test_wvht['ds'].max()
    periods_wvht = (last_test_date_wvht - last_train_date_wvht).days
    
    # Create a future dataframe for WVHT
    future_wvht = pd.DataFrame({'ds': pd.date_range(start=last_train_date_wvht + pd.Timedelta(days=1), 
                                                    end=last_test_date_wvht, freq='D')})
    
    # Combine train data and future data
    full_wvht = pd.concat([train_wvht[['ds', 'y', 'WTMP']], future_wvht], ignore_index=True)
    
    # Merge predicted WTMP into full_wvht for future dates
    wtmp_forecast_test['ds_m_d'] = wtmp_forecast_test['ds'].dt.strftime('%m-%d')
    full_wvht['ds_m_d'] = full_wvht['ds'].dt.strftime('%m-%d')
    
    full_wvht = pd.merge(full_wvht, wtmp_forecast_test[['ds_m_d', 'WTMP_pred']], on='ds_m_d', how='left')
    
    # Where WTMP_pred is available, use it instead of actual WTMP (for future dates)
    full_wvht['WTMP'] = full_wvht['WTMP'].fillna(full_wvht['WTMP_pred'])
    
    # Fit Prophet model for WVHT with WTMP as a regressor
    wvht_model = Prophet(yearly_seasonality=True, interval_width=0.70)
    wvht_model.add_regressor('WTMP')
    
    # Train only on historical data
    train_wvht_for_fit = full_wvht[full_wvht['ds'] < train_cutoff].dropna(subset=['y', 'WTMP'])
    wvht_model.fit(train_wvht_for_fit[['ds', 'y', 'WTMP']])
    
    # Predict WVHT
    wvht_forecast = wvht_model.predict(full_wvht[['ds', 'WTMP']])
    wvht_forecast_test = wvht_forecast[wvht_forecast['ds'] >= test_start].copy()
    wvht_forecast_test['ds_m_d'] = wvht_forecast_test['ds'].dt.strftime('%m-%d')

    # Evaluate WVHT
    test_merged = pd.merge(test_wvht[['ds', 'y']], 
                           wvht_forecast_test[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], 
                           on='ds', how='inner')
    mae_wvht = mean_absolute_error(test_merged['y'], test_merged['yhat'])
    print(f"Mean Absolute Error (WVHT) on 2024 Test Data for {station_id}: {mae_wvht}")
    
    # Evaluate WTMP
    test_merged_wtmp = pd.merge(test_wtmp[['ds', 'y']], 
                                wtmp_forecast_test[['ds', 'WTMP_pred', 'WTMP_pred_lower', 'WTMP_pred_upper']], 
                                on='ds', how='inner')
    mae_wtmp = mean_absolute_error(test_merged_wtmp['y'], test_merged_wtmp['WTMP_pred'])
    print(f"Mean Absolute Error (WTMP) on 2024 Test Data for {station_id}: {mae_wtmp}")

    # Merge WTMP predictions into final output
    final_merged = pd.merge(
        wvht_forecast_test, 
        wtmp_forecast_test[['ds_m_d', 'WTMP_pred', 'WTMP_pred_lower', 'WTMP_pred_upper']], 
        on='ds_m_d', 
        how='left'
    )

    # Add station_id
    final_merged['station_id'] = station_id
    
    # Rename ds_m_d to ds (month-day format)
    final_merged['ds'] = final_merged['ds_m_d']  # ds column now holds month-day format
    
    # Output columns (using ds instead of ds_m_d)
    output_df = final_merged[['station_id', 'ds', 
                              'yhat', 'yhat_lower', 'yhat_upper', 
                              'WTMP_pred', 'WTMP_pred_lower', 'WTMP_pred_upper']]
    
    # Save to CSV
    if first_run:
        output_df.to_csv(output_file, index=False)
        first_run = False
    else:
        output_df.to_csv(output_file, index=False, mode='a', header=False)
    # Plot WVHT Actual vs Predicted
    plt.figure(figsize=(10, 6))
    plt.plot(test_merged['ds'], test_merged['y'], label='Actual WVHT', marker='o')
    plt.plot(test_merged['ds'], test_merged['yhat'], label='Predicted WVHT', marker='o')
    plt.fill_between(test_merged['ds'], test_merged['yhat_lower'], test_merged['yhat_upper'], 
                     color='blue', alpha=0.2, label='WVHT Confidence Interval')
    plt.title(f'WVHT: Actual vs. Predicted with Confidence Intervals ({station_id})')
    plt.xlabel('Date')
    plt.ylabel('WVHT')
    plt.grid(True)
    plt.legend()
    # Save the figure instead of showing it
    plt.savefig(os.path.join(plots_dir, f"{station_id}_WVHT.png"))
    plt.close()

    # Plot WTMP Actual vs Predicted
    plt.figure(figsize=(10, 6))
    plt.plot(test_merged_wtmp['ds'], test_merged_wtmp['y'], label='Actual WTMP', marker='o', color='orange')
    plt.plot(test_merged_wtmp['ds'], test_merged_wtmp['WTMP_pred'], label='Predicted WTMP', marker='o', color='red')
    plt.fill_between(test_merged_wtmp['ds'], test_merged_wtmp['WTMP_pred_lower'], test_merged_wtmp['WTMP_pred_upper'], 
                     color='red', alpha=0.2, label='WTMP Confidence Interval')
    plt.title(f'WTMP: Actual vs. Predicted with Confidence Intervals ({station_id})')
    plt.xlabel('Date')
    plt.ylabel('WTMP')
    plt.grid(True)
    plt.legend()
    # Save the figure instead of showing it
    plt.savefig(os.path.join(plots_dir, f"{station_id}_WTMP.png"))
    plt.close()
print("All forecasts (with WTMP predictions and confidence intervals) saved to", output_file)

print("All plots saved in", plots_dir)