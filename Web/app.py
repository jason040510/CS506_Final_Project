from datetime import datetime
from flask import Flask, jsonify, request, render_template
import pandas as pd
from make_images import make_images
import os

app = Flask(__name__)

# Load CSV data
data = pd.read_csv('../forecast.csv')  # Ensure this file exists and is correctly formatted

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')  # Ensure `index.html` exists in the `templates/` folder

@app.route('/get_predictions', methods=['POST'])
def get_predictions():
    """
    Handle predictions based on user input, filter by wave height,
    and include water temperature, outfit suggestions, and forecast graphs.
    """
    try:
        # Parse JSON request data
        data_json = request.get_json()
        wave_height = float(data_json.get('wave_height', 0))
        num_days = int(data_json.get('num_days', 1))
        vacation_start_date = data_json.get('start_date', '')
        vacation_end_date = data_json.get('end_date', '')

        # Validate date inputs
        if not vacation_start_date or not vacation_end_date:
            raise ValueError("Start date and end date must be provided.")

        # Parse user-provided dates
        start_date = datetime.strptime(vacation_start_date, "%Y-%m-%d")
        end_date = datetime.strptime(vacation_end_date, "%Y-%m-%d")

        # Validate dataset columns
        required_columns = {
            'station_id', 'ds', 'yhat', 'yhat_lower', 'yhat_upper',
            'WTMP_pred', 'WTMP_pred_lower', 'WTMP_pred_upper'
        }
        if not required_columns.issubset(data.columns):
            raise ValueError("Dataset does not have the required columns.")

        # Convert `ds` to full_date in the main dataset
        data['full_date'] = pd.to_datetime(f"{datetime.now().year}-" + data['ds'], format="%Y-%m-%d")

        # Adjust for multi-year date ranges
        if start_date.year > datetime.now().year or end_date.year > datetime.now().year:
            data['full_date'] = pd.to_datetime(f"{end_date.year}-" + data['ds'], format="%Y-%m-%d")

        # Filter data for the selected date range
        vacation_data = data[
            (data['full_date'] >= start_date) &
            (data['full_date'] <= end_date)
        ].copy()

        # If no data in the selected range, suggest 3 closest dates outside the range
        if vacation_data.empty:
            return suggest_alternative_dates(data, start_date, end_date, wave_height, num_days)

        # Find the best `num_days` vacation windows
        response = suggest_vacation_windows(vacation_data, wave_height, num_days)

        # Get the best windows
        top_windows = response.get('top_windows', [])
        if not top_windows:
            return jsonify({
                'message': "No suitable vacation windows found.",
                'html': "No matches available.",
                'outfit_suggestion': "No outfit suggestion available.",
                'graphs': []
            })

        graph_paths = []
        for idx, (window, _) in enumerate(top_windows):
            station_id = window.iloc[0]['station_id']
            window_start = window['full_date'].min().strftime('%Y-%m-%d')
            window_end = window['full_date'].max().strftime('%Y-%m-%d')

            # Generate graphs for each station and time range
            input_file = f"../CleanedData/{station_id}.csv"  # Adjust for relative path
            if not os.path.exists(input_file):
                print(f"File not found: {input_file}")
                continue

            try:
                wvht_graph, wtmp_graph = make_images(input_file, station_id, window_start, window_end)
                graph_paths.append({'location': station_id, 'wvht': wvht_graph, 'wtmp': wtmp_graph})
            except Exception as e:
                print(f"Error generating graphs for {station_id}: {e}")

        # Calculate the average water temperature for the best vacation window
        best_window = top_windows[0][0]
        avg_temp = best_window['WTMP_pred'].mean()
        outfit_suggestion = get_outfit_suggestion(avg_temp)
        outfit_message = f"For an average water temperature of {avg_temp:.2f}°C: {outfit_suggestion}"

        # Return response with the generated graphs and suggestions
        return jsonify({
            'message': response.get('message', "Here are your top matches:"),
            'html': response.get('html', ""),
            'outfit_suggestion': outfit_message,
            'graphs': graph_paths
        })

    except ValueError as ve:
        return jsonify({'error': f"Input Error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({'error': f"Unexpected Error: {str(e)}"}), 500

def get_outfit_suggestion(temp):
    """
    Suggest a surfing outfit based on the water temperature.
    """
    if temp < 15:
        return "A 4/3mm or 5/4/3mm full-length wetsuit is recommended."
    elif 15 <= temp < 20:
        return "A 3/2mm wetsuit is ideal."
    elif 20 <= temp < 24:
        return "A 2mm shorty will be sufficient."
    elif 24 <= temp <= 25:
        return "A Thermolycra or neoprene top is usually recommended."
    else:
        return "A bathing suit or rashguard is sufficient."

def suggest_vacation_windows(data, wave_height, num_days):
    """
    Suggest the top 3 vacation windows of `num_days` consecutive days 
    based on wave height differences within the given range.
    
    This function ensures that each suggested window comes from a distinct station.
    """
    try:
        data['diff'] = abs(data['yhat'] - wave_height)
        vacation_windows = []

        # Identify potential windows
        for i in range(len(data) - num_days + 1):
            window = data.iloc[i:i + num_days]
            # Ensure all rows in this window are from the same station
            if window['station_id'].nunique() == 1:
                min_diff = window['diff'].sum()
                vacation_windows.append((window, min_diff))

        # Sort windows by their total difference
        vacation_windows.sort(key=lambda x: x[1])

        # Now ensure we pick top windows from distinct stations
        unique_station_windows = []
        used_stations = set()
        for window, diff_val in vacation_windows:
            station_id = window.iloc[0]['station_id']
            if station_id not in used_stations:
                unique_station_windows.append((window, diff_val))
                used_stations.add(station_id)
            if len(unique_station_windows) == 3:
                break

        if not unique_station_windows:
            return {'message': "No suitable vacation windows found.", 'html': "", 'top_windows': []}

        # Prepare the HTML suggestions
        suggestions = []
        for window, _ in unique_station_windows:
            suggestion = [
                f"{row['full_date'].strftime('%Y-%m-%d')} - {row['station_id'].split('_')[0]}, "
                f"Wave height: {row['yhat']:.2f}m, Water Temp: {row['WTMP_pred']:.2f}°C"
                for _, row in window.iterrows()
            ]
            suggestions.append("<br>".join(suggestion))

        return {
            'message': "Here are the top 3 vacation windows:",
            'html': "<br><br>".join(suggestions),
            'top_windows': unique_station_windows
        }

    except Exception as e:
        return {'message': f"Error suggesting vacation windows: {str(e)}", 'html': "", 'top_windows': []}

@app.route('/clear_images', methods=['POST'])
def clear_images():
    """
    Clear all files in the forecast_images folder.
    """
    try:
        folder_path = './static/forecast_images'  # Adjust the path if necessary
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return jsonify({'message': 'Forecast images cleared successfully.'})
        else:
            return jsonify({'error': 'Forecast images folder does not exist.'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to clear forecast images: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)