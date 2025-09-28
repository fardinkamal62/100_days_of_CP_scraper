import requests
import csv
import datetime
from datetime import timezone
import os
import time
from collections import defaultdict
import sys

class Codeforces100DayTracker:
    def __init__(self, handles_file='handles.txt', progress_file='progress.csv', daily_log_file='daily_log.csv', start_date=None, fetch_date=None):
        self.handles_file = handles_file
        self.progress_file = progress_file
        self.daily_log_file = daily_log_file
        self.base_url = 'https://codeforces.com/api/'
        
        if fetch_date:
            self.fetch_date = fetch_date
        else:
            self.fetch_date = datetime.date.today()

        if start_date:
            self.start_date = start_date
        else:
            self.start_date = datetime.date(2025, 9, 1)

        self.total_days = 100
        
    def load_handles(self):
        """Load Codeforces handles from a text file"""
        if not os.path.exists(self.handles_file):
            # Create a default file with example handles if none exists
            with open(self.handles_file, 'w') as f:
                f.write("fardinkamal62\n")
                f.write("tourist\n")
                f.write("jiangly\n")
            
        with open(self.handles_file, 'r') as f:
            handles = [line.strip() for line in f if line.strip()]
        return handles
    
    def get_user_submissions(self, handle, count=50):
        """Get recent submissions for a user from Codeforces API"""
        url = f"{self.base_url}user.status?handle={handle}&from=1&count={count}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    return data['result']
            return []
        except requests.exceptions.RequestException:
            return []
    
    def check_today_submissions(self, submissions):
        """Check if there are any accepted submissions today"""
        today = self.fetch_date
        today_count = 0
        latest_submission = None
        
        for submission in submissions:
            if submission.get('verdict') == 'OK':
                # Create UTC+6 timezone
                utc_plus_6 = timezone(datetime.timedelta(hours=6))
                submission_time = datetime.datetime.fromtimestamp(
                    submission['creationTimeSeconds'], tz=utc_plus_6
                ).date()
                
                if submission_time == today:
                    today_count += 1
                    if not latest_submission or submission['creationTimeSeconds'] > latest_submission['creationTimeSeconds']:
                        latest_submission = submission
        
        return today_count, latest_submission
    
    def get_submission_link(self, submission):
        """Generate a link to the submission"""
        if not submission:
            return ""
        return f"https://codeforces.com/contest/{submission['contestId']}/submission/{submission['id']}"
    
    def load_existing_progress(self):
        """Load existing progress data from CSV"""
        data = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    handle = row['Handle']
                    data[handle] = row
        return data
    
    def get_current_day(self):
        """Calculate the current day of the challenge"""
        day_number = (self.fetch_date - self.start_date).days + 1
        return min(max(1, day_number), self.total_days)
    
    def update_progress_data(self, handle, today_solved, submission_link, existing_data):
        """Update user progress data with today's activity"""
        today_str = self.fetch_date.strftime('%Y-%m-%d')
        day_number = self.get_current_day()
        day_column = f"Day {day_number}"
        
        if handle in existing_data:
            # Update existing user
            user_data = existing_data[handle]
            last_updated = user_data['Last Updated']
            
            # Check if we already updated today
            if last_updated == today_str:
                # Keep the higher value if we're running multiple times in a day
                current_today = int(user_data['Today Solved'])
                user_data['Today Solved'] = max(current_today, today_solved)
                if today_solved > 0 and user_data['Submission Link'] == "":
                    user_data['Submission Link'] = submission_link
            else:
                # Check if yesterday was consecutive
                yesterday = (self.fetch_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                if last_updated == yesterday:
                    user_data['Day Streak'] = int(user_data['Day Streak']) + 1 if today_solved > 0 else 0
                elif today_solved > 0:
                    user_data['Day Streak'] = 1
                else:
                    user_data['Day Streak'] = 0
                    
                user_data['Total Solved'] = int(user_data['Total Solved']) + today_solved
                user_data['Today Solved'] = today_solved
                user_data['Last Updated'] = today_str
                user_data['Submission Link'] = submission_link
            
            # Update the day column
            user_data[day_column] = '1' if today_solved > 0 else '0'
        else:
            # New user
            user_data = {
                'Handle': handle,
                'Total Solved': str(today_solved),
                'Last Updated': today_str,
                'Day Streak': '1' if today_solved > 0 else '0',
                'Today Solved': str(today_solved),
                'Submission Link': submission_link
            }
            
            # Initialize all days to 0
            for day in range(1, self.total_days + 1):
                user_data[f"Day {day}"] = '0'
            
            # Set today's day
            user_data[day_column] = '1' if today_solved > 0 else '0'
            existing_data[handle] = user_data
        
        return existing_data
    
    def save_progress_data(self, data):
        """Save progress data to CSV"""
        # Create fieldnames
        fieldnames = ['Handle', 'Total Solved', 'Last Updated', 'Day Streak', 'Today Solved', 'Submission Link']
        for day in range(1, self.total_days + 1):
            fieldnames.append(f"Day {day}")
        
        with open(self.progress_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for user_data in data.values():
                writer.writerow(user_data)
    
    def update_daily_log(self, handle, today_solved, submission_link):
        """Update the daily log with today's activity"""
        today_str = self.fetch_date.strftime('%Y-%m-%d')
        day_number = self.get_current_day()
        
        # Check if entry already exists for today
        entry_exists = False
        updated_rows = []
        
        if os.path.exists(self.daily_log_file):
            with open(self.daily_log_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Date'] == today_str and row['Handle'] == handle:
                        # Update existing entry
                        row['Problems Solved'] = max(int(row['Problems Solved']), today_solved)
                        if today_solved > 0 and not row['Submission Link']:
                            row['Submission Link'] = submission_link
                        entry_exists = True
                    updated_rows.append(row)
        
        if not entry_exists and today_solved > 0:
            # Add new entry
            new_entry = {
                'Date': today_str,
                'Handle': handle,
                'Problems Solved': today_solved,
                'Submission Link': submission_link,
                'Day Number': day_number
            }
            updated_rows.append(new_entry)
        
        # Write back to file
        fieldnames = ['Date', 'Handle', 'Problems Solved', 'Submission Link', 'Day Number']
        with open(self.daily_log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
    
    def run(self):
        """Main method to run the tracker"""
        print("Starting 100-Day Codeforces Tracker")
        print(f"Challenge Start Date: {self.start_date}")
        print(f"Fetching submissions for: {self.fetch_date}")
        print(f"Current Day: {self.get_current_day()}\n")
        
        print("Loading handles...")
        handles = self.load_handles()
        print(f"Found {len(handles)} handles: {', '.join(handles)}")
        
        print("Loading existing progress data...")
        existing_data = self.load_existing_progress()
        
        # Create a copy of the data to track changes
        updated_data = existing_data.copy()
        daily_log_updates = []

        print("Checking today's activity...")
        for i, handle in enumerate(handles):
            print(f"Checking {handle} ({i+1}/{len(handles)})...")
            submissions = self.get_user_submissions(handle)
            today_solved, latest_submission = self.check_today_submissions(submissions)
            submission_link = self.get_submission_link(latest_submission)
            
            existing_data = self.update_progress_data(handle, today_solved, submission_link, existing_data)
            
            daily_log_updates.append({
                'handle': handle,
                'today_solved': today_solved,
                'submission_link': submission_link
            })
            # Be nice to the API
            time.sleep(0.5)
        
        # Print summary
        print("\n=== TODAY'S SUMMARY ===")
        today = self.fetch_date.strftime('%Y-%m-%d')
        day_number = self.get_current_day()
        print(f"Date: {today} (Day {day_number}/100)")
        print(f"{'Handle':<20} {'Today Solved':<12} {'Total Solved':<12} {'Day Streak':<10} {'Status':<10}")
        print("-" * 65)
        
        for handle in handles:
            if handle in existing_data:
                data = existing_data[handle]
                status = "✅" if int(data['Today Solved']) > 0 else "❌"
                print(f"{handle:<20} {data['Today Solved']:<12} {data['Total Solved']:<12} {data['Day Streak']:<10} {status:<10}")
            else:
                print(f"{handle:<20} {'0':<12} {'0':<12} {'0':<10} ❌")
        

        while True:
            choice = input("\nDo you want to save these changes? (y/n): ").lower()
            if choice in ['y', 'yes']:
                print("Saving progress data...")
                self.save_progress_data(updated_data)
                
                # Now save daily logs
                for update in daily_log_updates:
                    self.update_daily_log(
                        update['handle'], 
                        update['today_solved'], 
                        update['submission_link']
                    )
                
                print("Done! Results saved to:")
                print(f"  - Progress file: {self.progress_file}")
                print(f"  - Daily log: {self.daily_log_file}")
                break
            elif choice in ['n', 'no']:
                print("Changes discarded. No files were updated.")
                break
            else:
                print("Please enter 'y' or 'n'")

if __name__ == "__main__":    
    if len(sys.argv) > 1:
        fetch_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        start_date = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d').date() if len(sys.argv) > 2 else datetime.date(2025, 9, 1)
        tracker = Codeforces100DayTracker(fetch_date=fetch_date, start_date=start_date)
    else:
        tracker = Codeforces100DayTracker()

    tracker.run()