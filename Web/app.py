from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template
import pandas as pd

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
    and include water temperature in the output.
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
        data['full_date'] = pd.to_datetime("2024-" + data['ds'], format="%Y-%m-%d")

        # Filter data for the selected date range
        vacation_data = data[
            (data['full_date'] >= start_date) &
            (data['full_date'] <= end_date)
        ].copy()

        # If no data in the selected range, suggest 3 closest dates outside the range
        if vacation_data.empty:
            return suggest_alternative_dates(data, start_date, end_date, wave_height, num_days)

        # Find the best `num_days` vacation windows
        return suggest_vacation_windows(vacation_data, wave_height, num_days)

    except ValueError as ve:
        return jsonify({'error': f"Input Error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({'error': f"Unexpected Error: {str(e)}"}), 500

def suggest_vacation_windows(data, wave_height, num_days):
    """
    Suggest the top 3 vacation windows of `num_days` consecutive days 
    based on wave height differences within the given range.
    """
    try:
        # Calculate the absolute difference between `yhat` and wave height
        data['diff'] = abs(data['yhat'] - wave_height)

        # Find all possible `num_days` vacation windows
        vacation_windows = []
        for i in range(len(data) - num_days + 1):
            window = data.iloc[i:i + num_days]
            if len(window) == num_days:
                min_diff = window['diff'].sum()
                vacation_windows.append((window, min_diff))

        # Sort vacation windows by total difference and select the top 3
        top_windows = sorted(vacation_windows, key=lambda x: x[1])[:3]

        if not top_windows:
            return jsonify({'message': "No suitable vacation windows found.", 'html': ""})

        # Format suggestions
        suggestions = []
        for window, _ in top_windows:
            suggestion = [
                f"{row['full_date'].strftime('%Y-%m-%d')} - Station {row['station_id']}, "
                f"Wave height: {row['yhat']:.2f}m, Water Temp: {row['WTMP_pred']:.2f}°C"
                for _, row in window.iterrows()
            ]
            suggestions.append("<br>".join(suggestion))

        return jsonify({
            'message': "Here are the top 3 vacation windows:",
            'html': "<br><br>".join(suggestions)
        })
    except Exception as e:
        return jsonify({'error': f"Error suggesting vacation windows: {str(e)}"}), 500

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
            return jsonify({
                'message': "No alternative sets of dates found.",
                'html': ""
            })

        # Format suggestions
        suggestions = []
        for window, _ in top_windows:
            suggestion = [
                f"{row['full_date'].strftime('%Y-%m-%d')} - Station {row['station_id']}, "
                f"Wave height: {row['yhat']:.2f}m, Water Temp: {row['WTMP_pred']:.2f}°C"
                for _, row in window.iterrows()
            ]
            suggestions.append("<br>".join(suggestion))

        return jsonify({
            'message': "Here are the top 3 alternative vacation windows:",
            'html': "<br><br>".join(suggestions)
        })
    except Exception as e:
        return jsonify({'error': f"Error suggesting alternative dates: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)