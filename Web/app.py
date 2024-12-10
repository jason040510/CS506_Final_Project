from datetime import datetime, timedelta
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
        required_columns = {'station_id', 'ds', 'yhat', 'yhat_lower', 'yhat_upper',
                            'WTMP_pred', 'WTMP_pred_lower', 'WTMP_pred_upper'}
        if not required_columns.issubset(data.columns):
            raise ValueError("Dataset does not have the required columns.")

        # Convert `ds` to full_date in the main dataset
        current_year = datetime.now().year
        data['full_date'] = pd.to_datetime(f"{current_year}-" + data['ds'], format="%Y-%m-%d")

        if start_date.year > current_year or end_date.year > current_year:
            next_year = current_year + 1
            data['full_date'] = pd.to_datetime(f"{next_year}-" + data['ds'], format="%Y-%m-%d")

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

        # Get the best window
        best_window = response.get('best_window', None)
        if best_window is None or best_window.empty:
            return jsonify({
                'message': "No suitable vacation windows found.",
                'html': "No matches available.",
                'outfit_suggestion': "No outfit suggestion available.",
                'graphs': []
            })

        # Get the station ID and the date range from the best window
        best_station_id = best_window.iloc[0]['station_id']
        best_window_start = best_window['full_date'].min().strftime('%Y-%m-%d')
        best_window_end = best_window['full_date'].max().strftime('%Y-%m-%d')

        # Generate graphs for the best station and time range
        graph_paths = []
        input_file = f"../CleanedData/{best_station_id}.csv"  # Adjust for relative path
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            return jsonify({
                'message': "File for the selected station is missing.",
                'html': "No graphs generated.",
                'outfit_suggestion': "No outfit suggestion available.",
                'graphs': []
            })

        try:
            wvht_graph, wtmp_graph = make_images(input_file, best_station_id, best_window_start, best_window_end)
            graph_paths.append({'location': best_station_id, 'wvht': wvht_graph, 'wtmp': wtmp_graph})
        except Exception as e:
            print(f"Error generating graphs for {best_station_id}: {e}")

        # Calculate the average water temperature for the best vacation window
        avg_temp = best_window['WTMP_pred'].mean()
        outfit_suggestion = get_outfit_suggestion(avg_temp)
        outfit_message = f"For an average water temperature of {avg_temp:.2f}°C: {outfit_suggestion}"

        # Return response with the generated graphs and suggestions
        return jsonify({
            'message': response.get('message', "Here is your best match:"),
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
    """
    try:
        data['diff'] = abs(data['yhat'] - wave_height)
        vacation_windows = []
        station_ids = set()  # Use a set to hold unique station IDs
        
        for i in range(len(data) - num_days + 1):
            window = data.iloc[i:i + num_days]
            if len(window) == num_days:
                min_diff = window['diff'].sum()
                vacation_windows.append((window, min_diff))
                # Collect unique station IDs from the window
                station_ids.update(window['station_id'].unique())
        
        # Sort and pick the top 3
        top_windows = sorted(vacation_windows, key=lambda x: x[1])[:3]

        if not top_windows:
            return {'message': "No suitable vacation windows found.", 'html': "", 'best_window': None, 'station_ids': []}

        best_window = top_windows[0][0]  # The best window is the first in sorted list
        suggestions = []

        for window, _ in top_windows:
            suggestion = [
                f"{row['full_date'].strftime('%Y-%m-%d')} - {row['station_id'].split('_')[0]}, "
                f"Wave height: {row['yhat']:.2f}m, Water Temp: {row['WTMP_pred']:.2f}°C"
                for _, row in window.iterrows()
            ]
            suggestions.append("<br>".join(suggestion))

        return {
            'message': "Here are the top 3 vacation windows:",
            'html': "<br><br>".join(suggestions),
            'best_window': best_window,
            'station_ids': list(station_ids)  # Convert set to list for output
        }
    except Exception as e:
        return {'message': f"Error suggesting vacation windows: {str(e)}", 'html': "", 'best_window': None, 'station_ids': []}

def suggest_alternative_dates(data, start_date, end_date, wave_height, num_days):
    """
    Suggest the 3 best permutations of `num_days` consecutive days after the selected range
    based on wave height differences.
    """
    try:
        # Filter data after the selected range
        future_data = data[data['full_date'] > end_date].copy()

        # Calculate the absolute difference between `yhat` and the desired wave height
        future_data['diff'] = abs(future_data['yhat'] - wave_height)

        # Sort future data by date to ensure chronological order
        future_data = future_data.sort_values('full_date').reset_index(drop=True)

        # Find the best permutations of `num_days` consecutive days
        vacation_windows = []
        for i in range(len(future_data) - num_days + 1):
            streak = future_data.iloc[i:i + num_days]
            if len(streak) == num_days:
                total_diff = streak['diff'].sum()
                vacation_windows.append((streak, total_diff))

        # Sort the matches by total difference and pick the top 3
        top_windows = sorted(vacation_windows, key=lambda x: x[1])[:3]

        if not top_windows:
            return {"message": "No alternative sets of dates found.", "html": ""}

        # Format suggestions
        suggestions = []
        for window, _ in top_windows:
            suggestion = [
                f"{row['full_date'].strftime('%Y-%m-%d')} - {row['station_id'].split('_')[0]}, "
                f"Wave height: {row['yhat']:.2f}m, Water Temp: {row['WTMP_pred']:.2f}°C"
                for _, row in window.iterrows()
            ]
            suggestions.append("<br>".join(suggestion))

        return {
            "message": "Here are the top 3 alternative vacation windows:",
            "html": "<br><br>".join(suggestions)
        }
    except Exception as e:
        return {"error": f"Error suggesting alternative dates: {str(e)}"}
    
import os
import shutil

@app.route('/clear_images', methods=['POST'])
def clear_images():
    """
    Clear all files in the forecast_images folder.
    """
    try:
        folder_path = './static/forecast_images'  # Adjust the path if necessary
        if os.path.exists(folder_path):
            # Remove all files in the folder
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