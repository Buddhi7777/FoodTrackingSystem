# FoodTrackingSystem
A simple Flask-based web application to manage student attendance and meal tracking. This project helps admins and students keep track of attendance records while also monitoring meals provided in the campus mess.
**Features**
Student Attendance Tracking – records daily student attendance.

 Meal Tracking System – monitors meals taken by students.

 Admin Panel – admin can reset counts daily and manage records.

 Responsive UI – clean web interface built with HTML, CSS, and JS.

 Tech Stack

Backend: Python (Flask)

Frontend: HTML, CSS, JavaScript

Database/Storage: Text files (for attendance & meal records)

FoodTrackingSystem/
│── app.py              # Main Flask app
│── main.py             # Additional script/runner
│── data_handler.py     # Attendance & meal data handling
│── attendance.txt      # Storage file
│
├── /templates          # HTML pages
│     ├── index.html
│     ├── admin.html
│     ├── layout.html
│
├── /static             # Static files
│     ├── /css/custom.css
│     ├── /js/script.js
