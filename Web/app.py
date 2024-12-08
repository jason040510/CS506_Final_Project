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
    Handle predictions based on user input and suggest alternatives if no matches are found.
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
        required_columns = {'station_id', 'ds', 'yhat', 'yhat_lower', 'yhat_upper'}
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
            # Calculate the center of the selected range
            selected_range_center = start_date + (end_date - start_date) / 2

            # Exclude dates within the range and find closest dates
            data_outside_range = data[
                (data['full_date'] < start_date) | (data['full_date'] > end_date)
            ].copy()
            if data_outside_range.empty:
                raise ValueError("No data available for alternative suggestions.")

            # Calculate the absolute difference between each date and the range center
            data_outside_range['date_diff'] = abs(data_outside_range['full_date'] - selected_range_center)
            closest_dates = data_outside_range.nsmallest(3, 'date_diff')

            # Format the suggestions
            suggestions = [
                f"{row['full_date'].strftime('%Y-%m-%d')} at station {row['station_id']} "
                f"(Wave height: {row['yhat']:.2f}m)"
                for _, row in closest_dates.iterrows()
            ]
            return jsonify({
                'message': "No matches found in the selected range. Here are 3 alternative suggestions:",
                'recommendations': suggestions
            })

        # Calculate the absolute difference between `yhat` and `wave_height`
        vacation_data.loc[:, 'diff'] = abs(vacation_data['yhat'] - wave_height)

        # Find matches for consecutive days
        consecutive_matches = find_consecutive_matches(vacation_data, num_days)
        if consecutive_matches:
            return jsonify({
                'message': "Here are your best matches!",
                'html': consecutive_matches
            })

        # No consecutive matches found
        return jsonify({'message': "No matches found for the specified range."})

    except ValueError as ve:
        return jsonify({'error': f"Input Error: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({'error': f"Unexpected Error: {str(e)}"}), 500


def find_consecutive_matches(vacation_data, num_days):
    """
    Find matches for consecutive days based on wave height differences and the desired number of days.
    """
    try:
        # Sort data by full_date to ensure chronological order
        vacation_data = vacation_data.sort_values('full_date')

        # Keep track of the current streak of consecutive days
        current_streak = []
        all_matches = []

        for i in range(len(vacation_data)):
            if not current_streak:
                # Start a new streak with the current row
                current_streak.append(vacation_data.iloc[i])
            else:
                # Get the last date in the current streak
                last_date = current_streak[-1]['full_date']

                # Check if the current row's date is exactly one day after the last date
                if vacation_data.iloc[i]['full_date'] == last_date + timedelta(days=1):
                    current_streak.append(vacation_data.iloc[i])
                else:
                    # If not consecutive, reset the streak
                    current_streak = [vacation_data.iloc[i]]

            # If the streak reaches the desired number of days, store it as a match
            if len(current_streak) == num_days:
                # Format match details
                match_details = [
                    f"{row['full_date'].strftime('%Y-%m-%d')} at station {row['station_id']} "
                    f"(Wave height: {row['yhat']:.2f}m)"
                    for _, row in enumerate(current_streak)
                ]
                all_matches.append("<br>".join(match_details))
                current_streak = []  # Reset streak after recording a match

        # Return all matches formatted as HTML
        return "<br><br>".join(all_matches) if all_matches else None

    except Exception as e:
        return f"Error finding consecutive matches: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)