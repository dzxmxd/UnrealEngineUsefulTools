import re
import pandas as pd
import sys
import os

# 兼容下 MemReport
def ensure_timestamp_and_frame(line):
    # 正则表达式匹配 [时间戳][帧号] 开头
    timestamp_frame_regex = re.compile(r"^\[\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3}\]\[\d+\]")

    # 检查是否以 [时间戳][帧号] 开头
    if not timestamp_frame_regex.match(line):
        # 如果不是，填充默认的时间戳和帧号
        default_timestamp = "[2025.01.01-00.00.00:000]"
        default_frame = "[0]"
        line = f"{default_timestamp}{default_frame}{line}"

    return line

def parse_log_to_excel(file_path):
    # Read log data from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        log_data = file.read()

    # Extracting lines that contain relevant data
    lines = log_data.splitlines()
    data_lines = []

    # Regex to match lines containing data
    regex = re.compile(r"^\[(.*?)\]\s+(\S+.*?)\s+(.*)$")

    # Extract the data
    headers = []
    for line in lines:
        line = ensure_timestamp_and_frame(line)
        match = regex.match(line)
        if match:
            timestamp, identifier, values = match.groups()
            value_columns = re.split(r"\s{2,}", values)
            if not headers:
                headers = ["Timestamp", "Identifier"] + value_columns
                continue
            data_lines.append([timestamp, identifier] + value_columns)

    # Create column names based on headers
    columns = headers

    # Convert extracted data into a DataFrame
    dataframe = pd.DataFrame(data_lines, columns=columns)

    # Convert numeric columns to the appropriate data type
    for col in columns[2:]:
        dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce')

    # Generate output file name based on input file name
    base_name = os.path.splitext(file_path)[0]
    output_file = f"{base_name}.xlsx"

    # Save to Excel file
    dataframe.to_excel(output_file, index=False)

    print(f"Data has been successfully saved to '{output_file}'.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_file_path>")
        sys.exit(1)

    log_file_path = sys.argv[1]
    parse_log_to_excel(log_file_path)