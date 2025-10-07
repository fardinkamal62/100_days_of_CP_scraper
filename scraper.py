import requests
import csv
import datetime
from datetime import timezone
import os
import time
from collections import defaultdict
import sys
from dotenv import load_dotenv

class Codeforces100DayTracker:
    def __init__(self, handles_file='handles.txt', progress_file='progress.csv', daily_log_file='daily_log.csv', start_date=None, fetch_date=None):
        self.handles_file = handles_file
        self.progress_file = progress_file
        self.daily_log_file = daily_log_file
        self.base_url = 'https://codeforces.com/api/'

        # Handle fetch_date logic
        if fetch_date in ['prev', -1]:
            self.fetch_date = datetime.date.today() - datetime.timedelta(days=1)
        elif fetch_date:
            self.fetch_date = fetch_date
        else:
            self.fetch_date = datetime.date.today()

        if start_date:
            self.start_date = start_date
        else:
            self.start_date = datetime.date(2025, 9, 1)

        self.total_days = 100

        load_dotenv()
        
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
    
    def send_to_discord(self, webhook_url, message):
        """Send a message to Discord using a webhook"""
        payload = {"content": message}
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                print("Message sent to Discord successfully.")
            else:
                print(f"Failed to send message to Discord. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to Discord: {e}")

    def generate_discord_message(self, day_number, total_remaining, eliminated_count, zero_elimination_streak, summary_message):
        """Generate a Discord message based on the day's results"""
        if eliminated_count == 0 and zero_elimination_streak > 1:
            # Zero elimination streak message
            return (
                f"Alhamdulillah! Alhamdulillah! Another day, another Zero-Elimination!! :star_struck: \n\n"
                f":rocket: Day {day_number} of **100 Days Of Problem Solving** Completed!\n\n"
                f"**Remaining:** {total_remaining} @100 Days of CPers ⛰️ !:muscle:\n"
                f"Shoutout to everyone! :tada:\n\n"
                f"**{zero_elimination_streak} Day** streak of Zero-Elimination!:tada: \n"
                f"Let's continue this Zero Elimination streak.... and crush Day {day_number + 1}! :fire:\n\n"
                f"```{summary_message}```"
            )
        elif eliminated_count == 0:
            # Zero eliminations message
            return (
                f":rocket: Day {day_number} of **100 Days Of Problem Solving** Completed!\n\n"
                f"Total Remaining: {total_remaining}\n"
                f"Eliminated: NONE!\n\n"
                f"Keep pushing, @100 Days of CPers ⛰️ !:muscle:\n"
                f"Shoutout to everyone who solved at least one problem today! :tada:\n\n"
                f"Don't get discouraged by the eliminations. This journey is about learning, growing, and challenging yourself. "
                f"Tomorrow is another opportunity to improve and excel.\n\n"
                f"Let's crush Day {day_number + 1}! :fire:\n\n"
                f"```{summary_message}```"
            )
        else:
            # One or more eliminations message
            return (
                f":rocket: Day {day_number} of **100 Days Of Problem Solving** Completed!\n\n"
                f"Total Remaining: {total_remaining}\n"
                f"Eliminated: {eliminated_count} :pensive:\n\n"
                f"Keep pushing, @100 Days of CPers ⛰️ !:muscle:\n"
                f"Shoutout to everyone who solved at least one problem today! :tada:\n\n"
                f"Don't get discouraged by the eliminations. This journey is about learning, growing, and challenging yourself. "
                f"Tomorrow is another opportunity to improve and excel.\n\n"
                f"Let's crush Day {day_number + 1}! :fire:\n\n"
                f"```{summary_message}```"
            )

    def calculate_zero_elimination_streak(self):
        """Calculate the streak of zero elimination days from the daily log"""
        if not os.path.exists(self.daily_log_file):
            return 0
        
        streak = 0
        with open(self.daily_log_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            previous_day = None
            for row in reversed(list(reader)):  # Read rows in reverse order
                current_day = int(row['Day Number'])
                if previous_day is not None and current_day != previous_day - 1:
                    break  # Break if days are not consecutive
                total_remaining = len([r for r in reader if int(r['Problems Solved']) > 0])
                total_handles = len(set(r['Handle'] for r in reader))
                if total_remaining == total_handles:
                    streak += 1
                else:
                    break
                previous_day = current_day
        return streak

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
        summary_lines = [
            f"Date: {today} (Day {day_number}/100)",
            f"{'Handle':<20} {'Today Solved':<12} {'Total Solved':<12} {'Day Streak':<10} {'Status':<10}",
            "-" * 65
        ]
        for handle in handles:
            if handle in existing_data:
                data = existing_data[handle]
                status = "✅" if int(data['Today Solved']) > 0 else "❌"
                summary_lines.append(
                    f"{handle:<20} {data['Today Solved']:<12} {data['Total Solved']:<12} {data['Day Streak']:<10} {status:<10}"
                )
            else:
                summary_lines.append(f"{handle:<20} {'0':<12} {'0':<12} {'0':<10} ❌")
        
        summary_message = "\n".join(summary_lines)
        print(summary_message)

        # Calculate eliminations and zero elimination streak
        total_remaining = len([handle for handle in handles if int(existing_data.get(handle, {}).get('Today Solved', 0)) > 0])
        eliminated_count = len(handles) - total_remaining
        zero_elimination_streak = self.calculate_zero_elimination_streak()

        # Generate and send the Discord message
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            discord_message = self.generate_discord_message(
                day_number=self.get_current_day(),
                total_remaining=total_remaining,
                eliminated_count=eliminated_count,
                zero_elimination_streak=zero_elimination_streak,
                summary_message=summary_message
            )
            try:
                self.send_to_discord(webhook_url, discord_message)
                print("Discord message sent successfully. Saving progress data automatically...")
                self.save_progress_data(updated_data)
                
                # Save daily logs
                for update in daily_log_updates:
                    self.update_daily_log(
                        update['handle'], 
                        update['today_solved'], 
                        update['submission_link']
                    )
                
                print("Data saved successfully!")
                print(f"  - Progress file: {self.progress_file}")
                print(f"  - Daily log: {self.daily_log_file}")
            except Exception as e:
                print(f"Failed to send Discord message or save data: {e}")
        else:
            print("Discord webhook URL not set. Skipping Discord notification.")

        # If webhook is not set or message fails, ask user to save manually
        if not webhook_url:
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
        if sys.argv[1] in ['prev', '-1']:
            fetch_date = 'prev'  # Pass 'prev' to trigger the logic in the constructor
        else:
            fetch_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        
        start_date = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d').date() if len(sys.argv) > 2 else datetime.date(2025, 9, 1)
        tracker = Codeforces100DayTracker(fetch_date=fetch_date, start_date=start_date)
    else:
        tracker = Codeforces100DayTracker()

    tracker.run()