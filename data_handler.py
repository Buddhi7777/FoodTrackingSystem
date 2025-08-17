import os
import json
import logging
from datetime import datetime, date

# Constants
DATA_DIR = "data"
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.txt")

def initialize_data_file():
    """Initialize the data directory and file if they don't exist"""
    try:
        # Create data directory if it doesn't exist
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # Create attendance file if it doesn't exist
        if not os.path.exists(ATTENDANCE_FILE):
            with open(ATTENDANCE_FILE, 'w') as f:
                # Initialize with empty JSON object (organized by date)
                f.write('{}')
        else:
            # Ensure the file contains a valid JSON object (not an array)
            with open(ATTENDANCE_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    try:
                        data = json.loads(content)
                        # If data is not a dict, reset it to an empty dict
                        if not isinstance(data, dict):
                            with open(ATTENDANCE_FILE, 'w') as f:
                                f.write('{}')
                                logging.debug("Attendance file was reset to empty object")
                    except json.JSONDecodeError:
                        # If not valid JSON, reset the file
                        with open(ATTENDANCE_FILE, 'w') as f:
                            f.write('{}')
                            logging.debug("Invalid JSON - Attendance file was reset to empty object")
                else:
                    # If file is empty, initialize it
                    with open(ATTENDANCE_FILE, 'w') as f:
                        f.write('{}')
                
        logging.debug(f"Data file initialized at {ATTENDANCE_FILE}")
    except Exception as e:
        logging.error(f"Error initializing data file: {str(e)}")
        raise

def load_attendance_data(date_str=None):
    """
    Load attendance data from the file
    
    Args:
        date_str (str, optional): If provided, return data for specific date.
                                 If None, return all data.
    
    Returns:
        dict: Data organized by date if date_str is None
        list: Records for the specified date if date_str is provided
    """
    try:
        with open(ATTENDANCE_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                data = json.loads(content)
                
                # Ensure data is a dictionary
                if not isinstance(data, dict):
                    logging.warning("Attendance data is not a dictionary. Resetting to empty object.")
                    # Write an empty dict directly instead of calling reset_attendance_data()
                    # to avoid circular imports
                    with open(ATTENDANCE_FILE, 'w') as f_write:
                        f_write.write('{}')
                    return {} if date_str is None else []
                
                # If a specific date is requested
                if date_str:
                    # Return data for that date, or empty list if no data for that date
                    return data.get(date_str, [])
                
                return data
            return {} if date_str is None else []
    except json.JSONDecodeError:
        logging.error("Invalid JSON in attendance file. Resetting to empty object.")
        # Write an empty dict directly to avoid circular import
        with open(ATTENDANCE_FILE, 'w') as f_write:
            f_write.write('{}')
        return {} if date_str is None else []
    except Exception as e:
        logging.error(f"Error loading attendance data: {str(e)}")
        # Write an empty dict directly to avoid circular import
        with open(ATTENDANCE_FILE, 'w') as f_write:
            f_write.write('{}')
        return {} if date_str is None else []
        
def get_available_dates():
    """Get list of dates that have attendance records"""
    try:
        data = load_attendance_data()
        # Sort dates in reverse chronological order (newest first)
        return sorted(data.keys(), reverse=True)
    except Exception as e:
        logging.error(f"Error getting available dates: {str(e)}")
        return []

def save_attendance_data(data):
    """Save attendance data to the file"""
    try:
        with open(ATTENDANCE_FILE, 'w') as f:
            f.write(json.dumps(data, indent=2))
    except Exception as e:
        logging.error(f"Error saving attendance data: {str(e)}")
        raise

def add_attendance_record(student_name, attendance_status, breakfast, lunch, dinner):
    """Add a new attendance record for today"""
    try:
        # Get today's date as string
        today = get_current_date()
        
        # Load all attendance data (dictionary by date)
        attendance_data = load_attendance_data()
        
        # Get today's records, or initialize if none exist
        today_records = attendance_data.get(today, [])
        
        # Create new record
        record = {
            "id": len(today_records) + 1,
            "student_name": student_name,
            "status": attendance_status,
            "meals": {
                "breakfast": breakfast,
                "lunch": lunch,
                "dinner": dinner
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add new record to today's data
        today_records.append(record)
        
        # Update the main data dictionary
        attendance_data[today] = today_records
        
        # Save updated data
        save_attendance_data(attendance_data)
        
        logging.debug(f"Added attendance record for {student_name} on {today}")
        return True
    except Exception as e:
        logging.error(f"Error adding attendance record: {str(e)}")
        raise

def reset_attendance_data():
    """Reset all attendance data"""
    try:
        save_attendance_data({})
        logging.debug("All attendance data reset")
    except Exception as e:
        logging.error(f"Error resetting attendance data: {str(e)}")
        raise
        
def reset_attendance_data_for_date(date_str=None):
    """
    Reset attendance data for a specific date
    
    Args:
        date_str (str, optional): Date in YYYY-MM-DD format. If None, use today's date.
    """
    try:
        # If no date is provided, use today's date
        if date_str is None:
            date_str = get_current_date()
        
        # Load all attendance data
        attendance_data = load_attendance_data()
        
        # Remove the data for the specified date
        if date_str in attendance_data:
            del attendance_data[date_str]
            
            # Save the updated data
            save_attendance_data(attendance_data)
            logging.debug(f"Attendance data for {date_str} reset")
        else:
            logging.debug(f"No data found for {date_str} to reset")
            
        return True
    except Exception as e:
        logging.error(f"Error resetting attendance data for date {date_str}: {str(e)}")
        raise

def get_attendance_stats(attendance_data):
    """Calculate attendance statistics"""
    total_students = len(attendance_data)
    coming_count = sum(1 for record in attendance_data if record.get('status') == 'Coming')
    not_coming_count = sum(1 for record in attendance_data if record.get('status') == 'Not Coming')
    
    breakfast_count = sum(1 for record in attendance_data 
                         if record.get('status') == 'Coming' and record.get('meals', {}).get('breakfast'))
    lunch_count = sum(1 for record in attendance_data 
                     if record.get('status') == 'Coming' and record.get('meals', {}).get('lunch'))
    dinner_count = sum(1 for record in attendance_data 
                      if record.get('status') == 'Coming' and record.get('meals', {}).get('dinner'))
    
    return {
        'total': total_students,
        'coming': coming_count,
        'not_coming': not_coming_count,
        'breakfast': breakfast_count,
        'lunch': lunch_count,
        'dinner': dinner_count
    }

def get_current_date():
    """Get current date in a formatted string for filenames"""
    return datetime.now().strftime("%Y-%m-%d")
