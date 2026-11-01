# '''
# A menu item ( eg: Dosa ) in a restaurant menu is available on a certain date or a certain weekday or a certain time of day.
# The objective of the application is to find available menu items for a given specific timestamp.

# Sample Input :
# itemname,available_timings,exclude_dates,exclude_days
# Dosa,"16:00-21:00,07:00-10:00,10:45-12:00","20-03-2024, 25-03-2024","Monday, Friday"
# '''


from flask import Flask, jsonify, request, render_template
from datetime import datetime, time, date
import csv
from io import StringIO
import os
from typing import Dict, List, Optional

# Initialize Flask application
app = Flask(__name__)

# Get the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "data2.csv")


def read_csv(filename: str) -> List[Dict[str, Optional[str]]]:
    """
    Read menu items from a CSV file.

    This function reads a CSV file containing menu items with their availability rules
    and returns a list of dictionaries, each representing a menu item.

    Args:
        filename (str): Path to the CSV file to read.

    Returns:
        List[Dict[str, Optional[str]]]: A list of dictionaries, where each dictionary
            contains the following keys:
            - itemname: Name of the menu item
            - available_timings: Time ranges when item is available (comma-separated)
            - exclude_dates: Dates when item is NOT available (comma-separated, DD-MM-YYYY format)
            - exclude_days: Weekdays when item is NOT available (comma-separated day names)

    Example:
        >>> items = read_csv("menu.csv")
        >>> print(items[0]["itemname"])
        "Dosa"
    """
    data = []
    with open(filename, "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            item = {
                "itemname": row.get("itemname", None),
                "available_timings": row.get("available_timings", None),
                "exclude_dates": row.get("exclude_dates", None),
                "exclude_days": row.get("exclude_days", None),
            }
            data.append(item)
    return data


def extract_data(data: bytes) -> Dict[str, Dict[str, str]]:
    """
    Extract menu data from uploaded CSV file bytes.

    This function processes raw CSV file data (bytes) and converts it into a dictionary
    structure where each menu item name maps to its availability details.

    Args:
        data (bytes): Raw CSV file content as bytes.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary where:
            - Keys are menu item names (itemname)
            - Values are dictionaries containing:
                - itemname: Name of the menu item
                - available_timings: Time ranges (comma-separated)
                - exclude_dates: Excluded dates (comma-separated, DD-MM-YYYY)
                - exclude_days: Excluded weekdays (comma-separated)

    Note:
        - Handles various line ending formats (\\n, \\r\\n, \\r)
        - Skips empty lines
        - Uses CSV reader to properly handle quoted fields

    Example:
        >>> csv_bytes = b'itemname,available_timings\\nDosa,"08:00-10:00"'
        >>> result = extract_data(csv_bytes)
        >>> result["Dosa"]["available_timings"]
        "08:00-10:00"
    """
    # Normalize line endings and split into lines
    decoded_data = (
        data.decode("utf-8")
        .strip()
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )
    columns = decoded_data[0].split(",")
    data_dict = {}
    for line in decoded_data[1:]:
        if not line.strip():  # Skip empty lines
            continue
        # Use CSV reader to handle quoted fields properly
        fields = next(csv.reader(StringIO(line), delimiter=",", quotechar='"'))
        data_dict[fields[0]] = {columns[i]: fields[i] for i in range(len(columns))}
    return data_dict


def is_time_in_range(start: time, end: time, current: time) -> bool:
    """
    Check if a current time falls within a time range.

    This function handles both normal time ranges (start < end) and ranges that span
    midnight (start > end), such as 22:00-02:00.

    Args:
        start (time): Start time of the range.
        end (time): End time of the range.
        current (time): Current time to check.

    Returns:
        bool: True if current time is within the range, False otherwise.

    Examples:
        >>> is_time_in_range(time(8, 0), time(18, 0), time(12, 0))
        True
        >>> is_time_in_range(time(22, 0), time(2, 0), time(23, 0))  # Spans midnight
        True
        >>> is_time_in_range(time(8, 0), time(18, 0), time(20, 0))
        False
    """
    if start <= end:
        # Normal range (e.g., 08:00 to 18:00)
        return start <= current <= end
    else:
        # Range spans midnight (e.g., 22:00 to 02:00)
        return start <= current or current <= end


def extract_items(
    data_dict: Dict[str, Dict[str, str]],
    current_time: time,
    current_date: date,
    current_day: str,
) -> List[str]:
    """
    Extract available menu items based on time, date, and day rules.

    This function filters menu items from the provided dictionary based on:
    1. Whether the current time falls within any of the item's available time ranges
    2. Whether the current date is in the item's exclude_dates list
    3. Whether the current weekday is in the item's exclude_days list

    Args:
        data_dict (Dict[str, Dict[str, str]]): Dictionary of menu items and their details.
            Each value must contain:
            - available_timings: Comma-separated time ranges (HH:MM-HH:MM)
            - exclude_dates: Comma-separated dates in DD-MM-YYYY format (optional)
            - exclude_days: Comma-separated weekday names (optional)
        current_time (time): Current time to check against available_timings.
        current_date (date): Current date to check against exclude_dates.
        current_day (str): Current weekday name (e.g., "Monday") to check against exclude_days.

    Returns:
        List[str]: List of menu item names that are currently available.

    Note:
        - Items are excluded if current_date is in exclude_dates
        - Items are excluded if current_day is in exclude_days
        - Items must have at least one time range that includes current_time
        - Empty exclude_dates and exclude_days are handled gracefully

    Example:
        >>> menu = {
        ...     "Dosa": {
        ...         "available_timings": "08:00-10:00,16:00-20:00",
        ...         "exclude_dates": "25-12-2024",
        ...         "exclude_days": "Monday"
        ...     }
        ... }
        >>> extract_items(menu, time(9, 0), date(2024, 12, 24), "Tuesday")
        ['Dosa']
    """
    result = []
    for item, details in data_dict.items():
        # Handle exclude_dates: Skip item if current date is excluded
        if details.get("exclude_dates", "").strip():
            exclude_dates = [
                datetime.strptime(date.strip(), "%d-%m-%Y").date()
                for date in details["exclude_dates"].split(",")
                if date.strip()
            ]
            if current_date in exclude_dates:
                continue

        # Handle exclude_days: Skip item if current weekday is excluded
        if details.get("exclude_days", "").strip():
            exclude_days_list = [
                day.strip() for day in details["exclude_days"].split(",") if day.strip()
            ]
            if current_day in exclude_days_list:
                continue

        # Check if current time falls within any available time range
        available = False
        for timing in details["available_timings"].split(","):
            start_time, end_time = map(
                lambda t: datetime.strptime(t.strip(), "%H:%M").time(),
                timing.split("-"),
            )
            if is_time_in_range(start_time, end_time, current_time):
                available = True
                break
        if available:
            result.append(item)
    return result


@app.route("/", methods=["GET"])
def index():
    """
    Serve the main web-based GUI page.

    This route renders the HTML template that provides the user interface for:
    - Setting the current timestamp
    - Uploading CSV files containing menu items
    - Viewing available menu items based on the uploaded data

    Returns:
        HTML: Rendered index.html template with the menu finder interface.

    Example:
        Navigate to http://localhost:5000/ in a browser to access the GUI.
    """
    return render_template("index.html")


@app.route("/api/set-time", methods=["GET"])
def set_current_time():
    """
    API endpoint to set the current timestamp in a cookie.

    This endpoint generates the current server time and stores it in a cookie.
    The stored timestamp is used by the /Menu/ endpoint to determine menu item availability.

    Returns:
        JSON: Response containing the current timestamp in ISO format.
            Example: {"current_time": "2024-12-24T14:30:00.123456"}

    Cookie:
        Sets a cookie named "current_time" with the ISO-formatted timestamp.

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:5000/api/set-time")
        >>> response.json()
        {"current_time": "2024-12-24T14:30:00.123456"}
    """
    current_time = datetime.now()
    response = jsonify({"current_time": current_time.isoformat()})
    response.set_cookie("current_time", current_time.isoformat())
    return response


@app.route("/Menu/", methods=["POST"])
def get_menu_item():
    """
    POST API endpoint to get available menu items based on uploaded CSV and stored timestamp.

    This endpoint processes an uploaded CSV file containing menu items with availability rules
    and returns a list of items that are currently available based on:
    - The timestamp stored in cookies (set via /api/set-time)
    - Time ranges specified in the CSV
    - Date and day exclusions specified in the CSV

    Request:
        Method: POST
        Content-Type: multipart/form-data
        Body:
            - data (file): CSV file with columns: itemname, available_timings, exclude_dates, exclude_days

    Headers:
        Cookie: Must contain "current_time" cookie set by /api/set-time

    Returns:
        JSON: Response containing available menu items.
            Success (200 OK):
                - If items found: {"Item available": ["Item1", "Item2", ...]}
                - If no items: {"Item available": None}
            Error (400 Bad Request):
                - "No file part" if CSV file is missing
                - "No current time set in cookies" if timestamp cookie is missing

    CSV Format:
        itemname,available_timings,exclude_dates,exclude_days
        Dosa,"16:00-21:00,07:00-10:00","20-03-2024","Monday, Friday"
        Pizza,"12:00-23:00","","Sunday"

    Example:
        >>> import requests
        >>> # First set the time
        >>> requests.get("http://localhost:5000/api/set-time")
        >>> # Then upload CSV
        >>> files = {"data": open("menu.csv", "rb")}
        >>> response = requests.post("http://localhost:5000/Menu/", files=files)
        >>> response.json()
        {"Item available": ["Dosa", "Pizza"]}
    """
    # Check if file is present in the request
    if "data" not in request.files:
        return "No file part", 400

    # Read and process the uploaded CSV file
    data_file = request.files["data"]
    file_content = data_file.read()
    data_dict = extract_data(file_content)

    # Retrieve timestamp from cookies
    current_time_str = request.cookies.get("current_time")
    if not current_time_str:
        return "No current time set in cookies", 400

    # Parse timestamp and extract time, date, and weekday
    current_time = datetime.fromisoformat(current_time_str)
    available_items = extract_items(
        data_dict, current_time.time(), current_time.date(), current_time.strftime("%A")
    )

    # Return results (None if no items available)
    return (
        jsonify({"Item available": available_items})
        if available_items
        else jsonify({"Item available": None})
    )


if __name__ == "__main__":
    # Run the Flask application in development mode
    # Starts the Flask development server on the default host (127.0.0.1) and port (5000)
    # Debug mode is enabled, which provides automatic reloading on code changes,
    # detailed error messages, and an interactive debugger
    #
    # Note: For production deployment, use a WSGI server like Gunicorn instead
    # Example: Run this file directly: python app.py
    #          Then access the application at: http://localhost:5000/
    app.run(debug=True)
