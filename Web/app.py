from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template
import pandas as pd

app = Flask(__name__)

# Load CSV data
data = pd.read_csv('forecast.csv')  # Ensure this file exists and is correctly formatted

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')  # Ensure `index.html` exists in the `templates/` folder

@app.route('/get_predictions', methods=['POST'])
def get_predictions():
    """
    Handle predictions based on user input.
    - Match based on the month and day (MM-DD), ignoring the year.
    """
    try:
        # Parse JSON request data
        data_json = request.get_json()
        wave_height = float(data_json.get('wave_height', 0))
        num_days = int(data_json.get('num_days', 1))  # Capture "Number of Days to Stay"
        vacation_start_date = data_json.get('start_date', '')
        vacation_end_date = data_json.get('end_date', '')

        # Validate date inputs
        if not vacation_start_date or not vacation_end_date:
            raise ValueError("Invalid start or end date provided.")

        # Parse user-provided dates
        start_date = datetime.strptime(vacation_start_date, "%Y-%m-%d")
        end_date = datetime.strptime(vacation_end_date, "%Y-%m-%d")

        # Add a "month_day" column to the dataset for cyclic matching
        data['month_day'] = data['ds']  # Ensure `ds` contains MM-DD format

        # Filter data for the selected month-day range
        vacation_data = data[
            (data['month_day'] >= start_date.strftime("%m-%d")) &
            (data['month_day'] <= end_date.strftime("%m-%d"))
        ]

        if vacation_data.empty:
            raise ValueError("No matching data found for the selected range.")

        # Calculate the absolute difference between `yhat` and `wave_height`
        vacation_data['diff'] = abs(vacation_data['yhat'] - wave_height)

        # Find matches for consecutive days
        consecutive_matches = find_consecutive_matches(vacation_data, num_days)
        if consecutive_matches:
            return jsonify({'message': "Here are your best matches!", 'html': consecutive_matches})

        # No consecutive matches found
        raise ValueError("No consecutive matches found for the specified range.")

    except Exception as e:
        return jsonify({'error': str(e)}), 400


def find_consecutive_matches(vacation_data, num_days):
    """
    Find consecutive matches for the specified number of days.
    """
    try:
        # Sort the data by the month-day for consecutive matching
        vacation_data['ds'] = pd.to_datetime("2024-" + vacation_data['month_day'], format="%Y-%m-%d")
        vacation_data = vacation_data.sort_values('ds')

        current_streak = []
        all_matches = []

        for i in range(len(vacation_data)):
            if not current_streak:
                current_streak.append(vacation_data.iloc[i])
            else:
                last_date = current_streak[-1]['ds']
                if vacation_data.iloc[i]['ds'] == last_date + timedelta(days=1):
                    current_streak.append(vacation_data.iloc[i])
                else:
                    current_streak = [vacation_data.iloc[i]]

            if len(current_streak) == num_days:
                # Prepare match details
                match_details = [
                    f"{day['ds'].strftime('%Y-%m-%d')} at station {day['station_id']} (Wave height: {day['yhat']:.2f}m)"
                    for day in current_streak
                ]
                all_matches.append("<br>".join(match_details))
                current_streak = []  # Reset streak after recording a match

        return "<br><br>".join(all_matches) if all_matches else None

    except Exception as e:
        return f"Error finding consecutive matches: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)