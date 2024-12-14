#!/bin/bash

# Initialize the database and create test data
python init_db.py

# Start the application with gunicorn
gunicorn wsgi:app
