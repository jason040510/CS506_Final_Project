import pandas as pd
import os
import glob
def drop_invalid_values(data, column, threshold=99):
    """
    Drop rows where the specified column has values greater than the threshold.

    Parameters:
        data (pd.DataFrame): The input DataFrame containing `#YY`, `MM`, `DD` and the target column.
        column (str): The column to check for invalid values.
        threshold (float): The threshold value. Values greater than this are considered invalid.

    Returns:
        pd.DataFrame: The cleaned DataFrame with invalid rows removed.
    """
    # Combine '#YY', 'MM', 'DD' into a single 'date' column
    data['date'] = pd.to_datetime(
        dict(year=data['#YY'], month=data['MM'], day=data['DD']),
        errors='coerce'
    )

    # Ensure there are no invalid or missing dates
    if data['date'].isnull().any():
        print("Warning: Some dates could not be parsed. Filling with nearby dates.")
        data['date'] = data['date'].fillna(method='ffill').fillna(method='bfill')

    # Drop rows where the column exceeds the threshold
    cleaned_data = data[data[column] < threshold]
    return cleaned_data.reset_index(drop=True)
def keep_max_wvht_per_day(data):
    """
    Keep only the row with the maximum WVHT value for each day and drop the rest.

    Args:
        data (pd.DataFrame): Input dataset with '#YY', 'MM', 'DD', and 'WVHT' columns.

    Returns:
        pd.DataFrame: Dataset with only one row per day, corresponding to the maximum WVHT.
    """
    # Combine '#YY', 'MM', 'DD' into a single date column
    data['date'] = pd.to_datetime(
        dict(year=data['#YY'], month=data['MM'], day=data['DD']),
        errors='coerce'
    )

    # Ensure that the 'date' column was created successfully
    if data['date'].isnull().any():
        print("Warning: Some dates could not be parsed. Dropping invalid rows.")
        data = data.dropna(subset=['date'])

    # Group by 'date' and find the row with the maximum WVHT for each day
    max_wvht_data = (
        data.loc[data.groupby('date')['WVHT'].idxmax()]
        .reset_index(drop=True)
    )

    # Drop the temporary 'date' column if not needed
    max_wvht_data = max_wvht_data.drop(columns=['date'])

    return max_wvht_data
def convert_txt_to_csv(input_folder, output_folder):
    try:
        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Walk through the directory and process all .txt files
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.endswith('.txt'):
                    # Full path to the input .txt file
                    input_file = os.path.join(root, file)
                    
                    # Define the output path, preserving the subfolder structure
                    relative_path = os.path.relpath(root, input_folder)
                    output_subfolder = os.path.join(output_folder, relative_path)
                    if not os.path.exists(output_subfolder):
                        os.makedirs(output_subfolder)
                    
                    output_file = os.path.join(output_subfolder, file.replace('.txt', '.csv'))
                    
                    # Read and process the file
                    df = pd.read_csv(
                        input_file,
                        delim_whitespace=True,
                        skiprows=2,
                        names=["#YY", "MM", "DD", "hh", "mm", "WDIR", "WSP", "D GST", "WVHT", "DPD", "APD", "MWD", "PRES", "ATMP", "WTMP", "DEWP", "VIS", "TIDE"]
                    )
                    # Select relevant columns
                    df = df[["#YY", "MM", "DD", "WVHT", "ATMP", "WTMP"]]
                    
                    # Save to CSV
                    df.to_csv(output_file, index=False)
                    print(f"Converted: {input_file} -> {output_file}")
        print("All files processed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def merge_csv_files_in_subfolders(input_folder, output_folder):
    try:
        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Walk through each sub-folder in the input folder
        for root, subdirs, _ in os.walk(input_folder):
            for subdir in subdirs:
                subdir_path = os.path.join(root, subdir)
                csv_files = glob.glob(os.path.join(subdir_path, "*.csv"))
                
                if csv_files:  # Proceed only if there are CSV files
                    # Create the output file path named after the sub-folder
                    output_file = os.path.join(output_folder, f"{subdir}.csv")
                    
                    # Initialize a DataFrame to merge data
                    merged_data = pd.DataFrame()
                    
                    for file in csv_files:
                        try:
                            # Read each CSV file into a DataFrame
                            df = pd.read_csv(file)
                            
                            # Append data to the merged DataFrame
                            merged_data = pd.concat([merged_data, df], ignore_index=True)
                            print(f"Processed file: {file}")
                        except Exception as e:
                            print(f"Error processing {file}: {e}")
                    
                    # Save the merged DataFrame to a new CSV file
                    merged_data.to_csv(output_file, index=False)
                    print(f"Merged files from {subdir_path} saved to: {output_file}")
        
        print("All sub-folder files have been merged successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Directory containing merged files

input_folder_csv = 'RawWaveData'
output_folder_csv = 'CSV_version_WaveData'

input_folder_merge = 'CSV_version_WaveData'
output_folder_merge = 'MergedData'

input_folder_clean = "MergedData"
output_folder_clean = "CleanedData"

convert_txt_to_csv(input_folder_csv, output_folder_csv)
merge_csv_files_in_subfolders(input_folder_merge, output_folder_merge)

# Ensure the output folder exists
if not os.path.exists(output_folder_clean):
    os.makedirs(output_folder_clean)

# Process each file in the folder
for file in os.listdir(input_folder_clean):
    if file.endswith('.csv'):
        file_path = os.path.join(input_folder_clean, file)
        try:
            # Load the data
            data = pd.read_csv(file_path)
            
            # Clean the 'WVHT' column
            data = drop_invalid_values(data, 'WVHT', threshold=99)
            data = keep_max_wvht_per_day(data)
            # Save the cleaned data to the output folder
            output_file_path = os.path.join(output_folder_clean, file)
            data.to_csv(output_file_path, index=False)
            print(f"Processed and saved cleaned data for: {file}")
        except Exception as e:
            print(f"Error processing file {file}: {e}")