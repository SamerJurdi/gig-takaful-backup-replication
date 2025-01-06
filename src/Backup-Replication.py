import os
import datetime
import zipfile
import shutil
import json
import traceback
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
exit = sys.exit


# Track if the process fails
process_success = True

# Load configuration from JSON file
config_file_path = "config.json"
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

SOURCE_DIRECTORY = config["source_directory"]
FILE_SERVER_DIRECTORY = config["file_server_directory"]
FILES_MAP = config["files"]
LOG_DIRECTORY = config["log_directory"]
EMAIL_SETTINGS = config["email_settings"]
DAYS_TO_DELETE = config["days_to_delete"]

# Set up logging function to create a structured log file by date
def setup_logger():
    today = datetime.datetime.now()
    year_dir = os.path.join(LOG_DIRECTORY, str(today.year))
    month_dir = os.path.join(year_dir, today.strftime("%B"))
    os.makedirs(month_dir, exist_ok=True)

    log_file_name = f"{today.strftime('%Y-%m-%d')}.log"
    log_file_path = os.path.join(month_dir, log_file_name)

    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Logger initialized")

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SETTINGS["sender"]
        msg["To"] = EMAIL_SETTINGS["recipient"]
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(EMAIL_SETTINGS["smtp_server"], EMAIL_SETTINGS["smtp_port"]) as server:
            server.starttls()
            #server.login(EMAIL_SETTINGS["username"], EMAIL_SETTINGS["password"])
            server.sendmail(EMAIL_SETTINGS["sender"], EMAIL_SETTINGS["recipient"], msg.as_string())
        logging.info("Notification email sent successfully.")
    except Exception as email_error:
        logging.error(f"Failed to send notification email: {email_error}")
        process_success = False

# Initialize logger
setup_logger()

# Calculate the names of the next days_ahead number of days of the week
def get_next_days(day_name, days_ahead):
    days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    start_index = days_of_week.index(day_name)
    return [days_of_week[(start_index + i) % 7] for i in range(1, days_ahead + 1)]

def delete_next_backups(current_day, days_to_delete):
    days_to_check = get_next_days(current_day, days_to_delete)
    for day in days_to_check:
        next_file_name = FILES_MAP.get(day)
        if next_file_name:
            # Find and delete old backups
            next_file_path = os.path.join(SOURCE_DIRECTORY, next_file_name)
            if os.path.exists(next_file_path):
                try:
                    os.remove(next_file_path)
                    logging.info(f"Deleted backup file for {day}: {next_file_path}")
                except Exception as delete_error:
                    logging.error(f"Failed to delete {next_file_path}: {delete_error}")
                    process_success = False
                    send_email(
                        subject=f"Backup Deletion Failed for {day}",
                        body=f"Failed to delete backup file {next_file_path}. Error: {delete_error}"
                    )
                    exit(1)

# Get the current day of the week (e.g., Monday, Tuesday)
day_of_week = datetime.datetime.now().strftime("%A")
logging.info(f"Script started for {day_of_week} backup process.")

# Get the file name for the current day
file_name = FILES_MAP.get(day_of_week)

if not file_name:
    logging.error(f"No file configured for {day_of_week}. Check the config file.")
    process_success = False
    send_email(
        subject=f"Backup Process Failed for {day_of_week}",
        body=f"No file configured for {day_of_week}. Please check the config file."
    )
    exit(1)

file_path = os.path.join(SOURCE_DIRECTORY, file_name)
name_without_extension = os.path.splitext(file_name)[0]
zip_file_name = f"{name_without_extension}.zip"
zip_file_path = os.path.join(SOURCE_DIRECTORY, zip_file_name)

try:
    # Check if the file for the current day exists
    if os.path.exists(file_path):
        logging.info(f"Found file {file_name} for {day_of_week}. Starting compression.")

        # Compress the file into a zip archive
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=file_name)
        logging.info(f"File {file_name} compressed successfully into {zip_file_name}.")

        # Transfer the zip file to the file server
        shutil.copy(zip_file_path, FILE_SERVER_DIRECTORY)
        logging.info(f"File {zip_file_name} transferred to {FILE_SERVER_DIRECTORY}.")

        delete_next_backups(day_of_week, DAYS_TO_DELETE)

    else:
        error_msg = f"File {file_name} not found for {day_of_week} in {SOURCE_DIRECTORY}. Process aborted."
        logging.error(error_msg)
        process_success = False
        send_email(
            subject=f"Backup Process Failed for {day_of_week}",
            body=error_msg
        )
        exit(1)

except Exception as e:
    error_msg = f"An error occurred during the process: {e}"
    logging.error(error_msg)
    logging.error(traceback.format_exc())
    process_success = False
    send_email(
        subject=f"Backup Process Failed for {day_of_week}",
        body=f"{error_msg}\n\n{traceback.format_exc()}"
    )
    exit(1)

finally:
    # Ensure that the zip file is removed, even if an error occurs during copy
    if os.path.exists(zip_file_path):
        try:
            os.remove(zip_file_path)
            logging.info("Temporary zip file removed successfully.")
        except Exception as cleanup_error:
            cleanup_msg = f"Error during cleanup: {cleanup_error}"
            logging.error(cleanup_msg)
            process_success = False
            send_email(
                subject=f"Backup Cleanup Error for {day_of_week}",
                body=cleanup_msg
            )
            exit(1)

    # Send success email if the process was successful
    if process_success:
        send_email(
            subject=f"Backup Process Successful for {day_of_week}",
            body=f"The backup file '{file_name}' was successfully compressed, transferred, and old backups deleted."
        )
