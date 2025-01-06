# Backup Replication Script

This script automates the daily backup process, including compressing files, transferring backups to a file server, deleting outdated backups, and sending notifications about the process. It is designed for flexibility and ease of use, leveraging a `config.json` file for configuration.

## Features

- **Day-Specific Backup**: Handles files dynamically based on the day of the week. Compresses them, transfers them, and deletes old backups.
- **Customizable**: Easily configurable via `config.json` to specify directories, files, and email settings.
- **Error Handling**: Logs detailed errors and sends email notifications for issues.
- **Logging**: Creates structured log files organized by year and month.
- **Cleanup**: Removes temporary files and old backups.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Script Workflow](#script-workflow)

## Installation

Before running the script, you’ll need to ensure you have Python installed on your system (Python 3.6 or higher recommended).

1. Clone the repository to your local machine:
    ```bash
    git clone https://github.com/SamerJurdi/gig-takaful-backup-replication.git backup-replication
    ```
2. Navigate into the cloned directory:
    ```
    cd backup-replication
    ```
3. Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To use the script, you’ll need to configure the `config.json` file first (see the [Configuration](#configuration) section below).

Once configured, you can run the script:

```bash
python Backup-Replication.py
```
The script will:

1. Check if the file for the current day of the week exists.
2. Compress the file into a .zip archive.
3. Transfer the zip file to a specified file server directory.
4. Delete old backup files for the next 4 days.

## Configuration
The script reads its configuration from the `config.json` file. You must set the paths for the source directory, file server directory, files to back up, logging directory, and email settings.

### Configuration Options:
- **source_directory**: Path to the directory where your source files are stored.
- **file_server_directory**: Path to the file server where the backups will be transferred.
- **files**: A mapping of weekdays to the filenames that should be backed up respectively.
- **log_directory**: Path to the directory where the logs will be stored.
- **email_settings**: SMTP email configuration to send notifications for successes, errors, and other updates.
- **days_to_delete**: <u>Number</u> of backups to be deleted starting from the oldest. Any number above 6 will delete all backups referenced in `files`.

### Notes:
- The script only works if the file for the current day exists in the `source_directory`.
- The backup file will be zipped and transferred to the `file_server_directory`.

## Script Workflow

The backup process follows these steps:

1. **Initialize Logging**: Sets up a log file for the current day under the `log_directory`.
2. **Read Configuration**: Loads the configuration from `config.json` to determine the source and backup locations.
3. **File Compression**: If the file for the current day exists in the `source_directory`, it will be compressed into a `.zip` archive.
4. **File Transfer**: The compressed backup is then transferred to the `file_server_directory`.
5. **Backup Cleanup**: The script will delete backups for the next 4 days (as configured) in the source directory to avoid accumulating unnecessary files.
6. **Error Handling and Email Notification**: If any errors occur during the process, they will be logged, and an email notification will be sent.

The script uses an SMTP server to send notifications. Successful completion of each step will trigger an email, while errors will be reported in detail.
