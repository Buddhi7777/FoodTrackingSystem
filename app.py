import os
import logging
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_file, Response
import data_handler
from fpdf import FPDF

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Admin password from environment variable
# Use default password only in development
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Initialize data file if it doesn't exist
data_handler.initialize_data_file()

@app.route('/')
def index():
    """
    Render the main page with the attendance form and current statistics
    """
    # Get date from query parameter, or use today's date
    date_str = request.args.get('date')
    if not date_str:
        date_str = data_handler.get_current_date()
    
    # Get available dates for the date selector
    available_dates = data_handler.get_available_dates()
    
    # Load attendance data for the specified date
    attendance_data = data_handler.load_attendance_data(date_str)
    
    # Calculate statistics
    stats = data_handler.get_attendance_stats(attendance_data)
    
    return render_template('index.html', 
                          stats=stats, 
                          attendance_data=attendance_data,
                          current_date=date_str,
                          available_dates=available_dates)

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    """Handle the attendance form submission"""
    try:
        student_name = request.form.get('student_name', '').strip()
        attendance_status = request.form.get('attendance_status')
        breakfast = 'breakfast' in request.form
        lunch = 'lunch' in request.form
        dinner = 'dinner' in request.form

        # Basic validation
        if not student_name:
            flash('Please enter your name', 'danger')
            return redirect(url_for('index'))
        
        if not attendance_status:
            flash('Please select your attendance status', 'danger')
            return redirect(url_for('index'))
            
        # Save the attendance data
        data_handler.add_attendance_record(student_name, attendance_status, breakfast, lunch, dinner)
        
        flash(f'Thank you {student_name}! Your attendance has been recorded.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error submitting attendance: {str(e)}")
        flash('An error occurred while submitting your attendance. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    """
    Render the admin page
    """
    # Check if the admin is logged in
    if not session.get('admin_logged_in'):
        return render_template('admin.html', logged_in=False)
    
    # Get date from query parameter, or use today's date
    date_str = request.args.get('date')
    
    # Get available dates for the date selector
    available_dates = data_handler.get_available_dates()
    
    if date_str:
        # Load attendance data for the specified date
        attendance_data = data_handler.load_attendance_data(date_str)
        
        # Calculate statistics for the specific date
        stats = data_handler.get_attendance_stats(attendance_data)
    else:
        # If no date specified, show data for all dates combined
        all_attendance_data = data_handler.load_attendance_data()
        
        # For the table, show records from all dates
        attendance_data = []
        for date_key, date_records in sorted(all_attendance_data.items(), reverse=True):
            for record in date_records:
                # Add date information to each record for display
                record_with_date = record.copy()
                record_with_date['date'] = date_key
                attendance_data.append(record_with_date)
        
        # Combined stats for all dates
        stats = {
            'total': 0,
            'coming': 0,
            'not_coming': 0,
            'breakfast': 0,
            'lunch': 0,
            'dinner': 0
        }
        
        # Calculate combined stats
        for _, records in all_attendance_data.items():
            date_stats = data_handler.get_attendance_stats(records)
            stats['total'] += date_stats['total']
            stats['coming'] += date_stats['coming']
            stats['not_coming'] += date_stats['not_coming']
            stats['breakfast'] += date_stats['breakfast']
            stats['lunch'] += date_stats['lunch']
            stats['dinner'] += date_stats['dinner']
    
    return render_template('admin.html', 
                          logged_in=True, 
                          attendance_data=attendance_data, 
                          stats=stats,
                          current_date=date_str,
                          available_dates=available_dates)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Handle admin login"""
    password = request.form.get('password')
    
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        flash('Admin login successful', 'success')
    else:
        flash('Invalid password', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    """Handle admin logout"""
    session.pop('admin_logged_in', None)
    flash('Admin logged out', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/reset', methods=['POST'])
def reset_attendance():
    """Reset all attendance data (admin only)"""
    if not session.get('admin_logged_in'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))
    
    reset_type = request.form.get('reset_type', 'all')
    date_str = request.form.get('date_str')
    
    if reset_type == 'all':
        # Reset all attendance data
        data_handler.reset_attendance_data()
        flash('All attendance data has been reset', 'success')
    else:
        # Reset data for the specified date
        if not date_str:
            date_str = data_handler.get_current_date()
            
        data_handler.reset_attendance_data_for_date(date_str)
        flash(f'Attendance data for {date_str} has been reset', 'success')
    
    # Redirect back to the appropriate admin page
    if date_str and reset_type != 'all':
        return redirect(url_for('admin', date=date_str))
    else:
        return redirect(url_for('admin'))

@app.route('/admin/export/csv')
@app.route('/admin/export/csv/<date_str>')
def export_csv(date_str=None):
    """
    Export attendance data as CSV file (admin only)
    
    Args:
        date_str (str, optional): Date in YYYY-MM-DD format. If None, export for all dates.
    """
    if not session.get('admin_logged_in'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))
    
    # Create a StringIO object for CSV writing
    si = io.StringIO()
    csv_writer = csv.writer(si)
    
    # Write header row with date column if exporting all dates
    if date_str:
        # Export for specific date
        attendance_data = data_handler.load_attendance_data(date_str)
        csv_writer.writerow(['ID', 'Student Name', 'Status', 'Breakfast', 'Lunch', 'Dinner', 'Timestamp'])
        
        # Write data rows for specific date
        for record in attendance_data:
            csv_writer.writerow([
                record['id'],
                record['student_name'],
                record['status'],
                'Yes' if record['meals']['breakfast'] else 'No',
                'Yes' if record['meals']['lunch'] else 'No',
                'Yes' if record['meals']['dinner'] else 'No',
                record['timestamp']
            ])
        
        # Filename with the specific date
        filename = f"attendance_data_{date_str}.csv"
    else:
        # Export for all dates
        all_attendance_data = data_handler.load_attendance_data()
        csv_writer.writerow(['Date', 'ID', 'Student Name', 'Status', 'Breakfast', 'Lunch', 'Dinner', 'Timestamp'])
        
        # Write data rows for all dates
        for date_key, records in all_attendance_data.items():
            for record in records:
                csv_writer.writerow([
                    date_key,
                    record['id'],
                    record['student_name'],
                    record['status'],
                    'Yes' if record['meals']['breakfast'] else 'No',
                    'Yes' if record['meals']['lunch'] else 'No',
                    'Yes' if record['meals']['dinner'] else 'No',
                    record['timestamp']
                ])
        
        # Filename with current date (for export time)
        filename = f"all_attendance_data_{data_handler.get_current_date()}.csv"
    
    # Create response
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route('/admin/export/pdf')
@app.route('/admin/export/pdf/<date_str>')
def export_pdf(date_str=None):
    """
    Export attendance data as PDF file (admin only)
    
    Args:
        date_str (str, optional): Date in YYYY-MM-DD format. If None, export all dates.
    """
    if not session.get('admin_logged_in'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('admin'))
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Student Attendance & Meal Tracking Report', 0, 1, 'C')
    
    if date_str:
        # Export for specific date
        pdf.cell(0, 10, f"Date: {date_str}", 0, 1, 'C')
        attendance_data = data_handler.load_attendance_data(date_str)
        stats = data_handler.get_attendance_stats(attendance_data)
        
        # Filename with the specific date
        filename = f"attendance_report_{date_str}.pdf"
    else:
        # Export for all dates
        pdf.cell(0, 10, f"Report Generated: {data_handler.get_current_date()}", 0, 1, 'C')
        
        # Load all dates data
        all_attendance_data = data_handler.load_attendance_data()
        
        # Combined stats will be calculated below
        stats = {
            'total': 0,
            'coming': 0,
            'not_coming': 0,
            'breakfast': 0,
            'lunch': 0,
            'dinner': 0
        }
        
        # Calculate combined stats
        for date_key, records in all_attendance_data.items():
            date_stats = data_handler.get_attendance_stats(records)
            stats['total'] += date_stats['total']
            stats['coming'] += date_stats['coming']
            stats['not_coming'] += date_stats['not_coming']
            stats['breakfast'] += date_stats['breakfast']
            stats['lunch'] += date_stats['lunch']
            stats['dinner'] += date_stats['dinner']
        
        # Filename for all dates
        filename = f"all_attendance_report_{data_handler.get_current_date()}.pdf"
    
    pdf.ln(10)
    
    # Statistics Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Attendance Summary', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(60, 8, f"Total Students: {stats['total']}", 0, 1)
    pdf.cell(60, 8, f"Coming: {stats['coming']}", 0, 1)
    pdf.cell(60, 8, f"Not Coming: {stats['not_coming']}", 0, 1)
    pdf.ln(5)
    
    pdf.cell(60, 8, f"Breakfast Count: {stats['breakfast']}", 0, 1)
    pdf.cell(60, 8, f"Lunch Count: {stats['lunch']}", 0, 1)
    pdf.cell(60, 8, f"Dinner Count: {stats['dinner']}", 0, 1)
    pdf.ln(10)
    
    # Attendance Records Tables
    if date_str:
        # Single date attendance records
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Attendance Records for {date_str}', 0, 1)
        
        # Table header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(10, 8, 'ID', 1, 0, 'C')
        pdf.cell(40, 8, 'Student Name', 1, 0, 'C')
        pdf.cell(25, 8, 'Status', 1, 0, 'C')
        pdf.cell(20, 8, 'Breakfast', 1, 0, 'C')
        pdf.cell(20, 8, 'Lunch', 1, 0, 'C')
        pdf.cell(20, 8, 'Dinner', 1, 0, 'C')
        pdf.cell(50, 8, 'Timestamp', 1, 1, 'C')
        
        # Table data
        pdf.set_font('Arial', '', 10)
        for record in attendance_data:
            pdf.cell(10, 8, str(record['id']), 1, 0, 'C')
            pdf.cell(40, 8, record['student_name'], 1, 0)
            pdf.cell(25, 8, record['status'], 1, 0, 'C')
            pdf.cell(20, 8, 'Yes' if record['meals']['breakfast'] else 'No', 1, 0, 'C')
            pdf.cell(20, 8, 'Yes' if record['meals']['lunch'] else 'No', 1, 0, 'C')
            pdf.cell(20, 8, 'Yes' if record['meals']['dinner'] else 'No', 1, 0, 'C')
            pdf.cell(50, 8, record['timestamp'], 1, 1, 'C')
    else:
        # Multiple dates attendance records
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Attendance Records by Date', 0, 1)
        
        # Process each date
        for date_key in sorted(all_attendance_data.keys(), reverse=True):
            records = all_attendance_data[date_key]
            
            if not records:
                continue
                
            # Date header
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'Date: {date_key}', 0, 1)
            
            # Table header
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(10, 8, 'ID', 1, 0, 'C')
            pdf.cell(40, 8, 'Student Name', 1, 0, 'C')
            pdf.cell(20, 8, 'Status', 1, 0, 'C')
            pdf.cell(15, 8, 'Breakfast', 1, 0, 'C')
            pdf.cell(15, 8, 'Lunch', 1, 0, 'C')
            pdf.cell(15, 8, 'Dinner', 1, 0, 'C')
            pdf.cell(40, 8, 'Time', 1, 1, 'C')
            
            # Table data for this date
            pdf.set_font('Arial', '', 9)
            for record in records:
                pdf.cell(10, 8, str(record['id']), 1, 0, 'C')
                pdf.cell(40, 8, record['student_name'][:20], 1, 0)
                pdf.cell(20, 8, record['status'], 1, 0, 'C')
                pdf.cell(15, 8, 'Yes' if record['meals']['breakfast'] else 'No', 1, 0, 'C')
                pdf.cell(15, 8, 'Yes' if record['meals']['lunch'] else 'No', 1, 0, 'C')
                pdf.cell(15, 8, 'Yes' if record['meals']['dinner'] else 'No', 1, 0, 'C')
                
                # Extract just the time portion from timestamp (assuming format "YYYY-MM-DD HH:MM:SS")
                time_part = record['timestamp'].split(' ')[1] if ' ' in record['timestamp'] else ''
                pdf.cell(40, 8, time_part, 1, 1, 'C')
            
            # Add spacing between date sections
            pdf.ln(5)
            
            # Check if we need a new page
            if pdf.get_y() > 250:
                pdf.add_page()
    
    # Create in-memory buffer for PDF
    pdf_output = io.BytesIO()
    
    # Get PDF as string and write to BytesIO
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    
    return send_file(
        pdf_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logging.error(f"Server error: {str(e)}")
    return render_template('index.html', error="Server error occurred. Please try again later."), 500
