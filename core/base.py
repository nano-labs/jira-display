import atexit
import json
from datetime import datetime, timedelta
from time import sleep
import traceback

import serial
from jira import JIRA

from core import info_log
from display.base import DisplayIssue, DisplayText


class JiraAPI:

    def __init__(self, config):
        self.config = config

        self.todo_status = self.config["status"]["todo"]
        self.in_progress_status = self.config["status"]["in_progress"]
        self.done_status = self.config["status"]["done"]
        self.project_id = self.config["project_id"]

        self.jira_api = JIRA(
            self.config["account_url"],
            basic_auth=(
                self.config["username"],
                self.config["token"]
            )
        )
        self.current_issue = None
        self.get_current_issue()

    def get_current_issue(self):
        self.current_issue = next(
            (issue for issue in self.get_my_issues(self.in_progress_status)),
            None
        )
        return self.current_issue

    def get_issue(self, issue_key):
        return self.jira_api.issue(issue_key)

    def get_my_issues(self, status_id=None):
        """Get all my issues of filter by status.

        Args:
            status (str): Options are "todo", "in_progress" and "done"

        """
        status_filter = ""
        if status_id:
            status_filter = " and status = {status}".format(status=status_id)

        query = (
            'assignee = currentUser() '
            'and project = {project_id}{status_filter} '
            'order by created desc'
        ).format(
            project_id=self.project_id,
            status_filter=status_filter
        )
        return list(self.jira_api.search_issues(query))

    def change_status(self, issue, status_id):
        """Change an issue's status.

        Args:
            issue: <JIRA Issue> object
            status (str): Options are "todo", "in_progress" and "done"

        """
        if issue.fields.status.id == status_id:
            return

        resolution_id = next(
            resolution["id"]
            for resolution in self.jira_api.transitions(issue)
            if resolution["to"]["id"] == status_id
        )
        info_log("Changing state of task {} to {}".format(issue, resolution_id))
        self.jira_api.transition_issue(issue, resolution_id)

    def start_issue(self, issue):
        """Change issue state to 'in progress' and any other in progress to 'todo'.

        Args:
            issue: <JIRA Issue> object

        """
        info_log("Starting task {}".format(issue))
        for in_progress in self.get_my_issues(self.in_progress_status):
            if not in_progress.id == issue.id:
                self.change_status(in_progress, self.todo_status)
        self.change_status(issue, self.in_progress_status)

    def add_time(self, issue, seconds):
        """Add worklog time to a issue."""
        seconds = max(int(seconds), 60)
        info_log("Add {} seconds to worklog to {}".format(seconds, issue))
        self.jira_api.add_worklog(issue.id, adjustEstimate="auto", timeSpentSeconds=seconds)


class Display:

    def __init__(self, config, manager):
        self.todo_status = config["status"]["todo"]
        self.in_progress_status = config["status"]["in_progress"]
        self.issue = None
        self.start_time = datetime.now()
        self.issue_preview = None
        self.bitmap = None
        self.current_screen = 'splash'
        self._image = None
        self.blinking = False
        self.blink_colon = False
        self._manager = manager

    def register_time(self):
        if self.issue and self.issue.fields.status.id == self.in_progress_status:
            delta = (datetime.now() - self.start_time).total_seconds()
            self._manager.api.add_time(self.issue, delta)
            self.issue = self._manager.api.get_issue(self.issue.key)
            self._manager.refresh_issues()
            self.start_time = datetime.now()

    def update(self):
        if self.current_screen == 'issue_selection':
            if not self.issue_preview:
                issue_text = "You do not have any tasks"
            else:
                issue_text = "{}: {}".format(self.issue_preview.key,
                                             self.issue_preview.fields.summary)
            self._image = DisplayText(issue_text).image

        elif self.current_screen == "issue":
            if self.issue.fields.status.id == self.in_progress_status:
                state = "running"
                elapsed = self.issue.fields.timespent or 0
                elapsed = (datetime.now() + timedelta(seconds=elapsed)) - self.start_time
                elapsed = elapsed.total_seconds()
                if (datetime.now() - self.start_time).total_seconds() >= 30 * 60:
                    self._manager.waiting_ack = True
                    self.blinking = not self.blinking
                clock = "{:02d}:{:02d}".format(int(elapsed / 60), int(elapsed % 60))
                if elapsed >= 60 * 60:  # one hour
                    elapsed = int(elapsed / 60)  # this variable become minutes
                    self.blink_colon = not self.blink_colon
                    clock = "{:02d}{}{:02d}".format(
                        int(elapsed / 60),
                        ";:"[self.blink_colon],
                        int(elapsed % 60)
                    )
            else:
                state = "paused"
                clock = None
                self._manager.timers.remove_by_tag("update_display")
            self._image = DisplayIssue(self.issue, state, clock,
                                       inversed_colors=self.blinking).image

    def save_file(self, filename):
        if self._image:
            self._image.save(filename)


class Timers:

    def __init__(self):
        """Timers definition.

        self.timers = {
            <datetime>: {
                "function": <function>,
                "tag": "some tag"
            },
            <datetime>: {
                "function": <function>,
                "tag": "some tag"
            },
        }
        """
        self.timers = {}

    def execute(self):
        """Exceture any due task e remove it from the queue."""
        for timer, task in list(self.timers.items()):
            if datetime.now() >= timer:
                self.timers.pop(timer)
                task["function"]()

    def add(self, due, function, tag=None):
        """Add a new timed function to the queue."""
        if not callable(function):
            raise Exception("timed function must be a callable")
        self.timers[due] = {"function": function, "tag": tag}

    def remove_by_tag(self, tag):
        """Remove any timed function matching tag."""
        for timer, task in list(self.timers.items()):
            if task["tag"] == tag:
                self.timers.pop(timer)


class Manager:

    def __init__(self, config):
        self.config = config
        self.serial = serial.Serial(config['serial_port'], 57600, timeout=1)
        self.api = JiraAPI(config)
        # self.serial = serial.Serial(config['serial_port'], 9600, timeout=1)
        self.issues = []
        self.display = Display(config, manager=self)
        self.clock = 10  # Hz
        self.timers = Timers()
        self.last_message = ("", datetime.now())
        self.waiting_ack = False
        self._last_iteration = datetime.now()

    def start(self):
        self.update_display()
        self.refresh_issues()
        if self.issues:
            self.display.current_screen = "issue"
        else:
            self.display.current_screen = "issue_selection"
        self.update_display()

    def refresh_issues(self):
        self.issues = self.api.get_my_issues(self.api.in_progress_status)
        self.issues.extend(self.api.get_my_issues(self.api.todo_status))
        if self.display.issue:
            self.display.issue = next(
                (i for i in self.issues if i.id == self.display.issue.id),
                self.issues[0] if self.issues else None
            )
        else:
            self.display.issue = self.issues[0] if self.issues else None
        self.issues = sorted(self.issues, key=lambda x: x.key)

    def navigate_next_issue(self, issues):
        self.timers.remove_by_tag("display_update")
        if self.display.current_screen == 'issue_selection':
            if not self.display.issue_preview:
                return
            current_issue = self.display.issue_preview
            for index, issue in enumerate(issues):
                if issue.id == current_issue.id:
                    if index >= len(issues) - 1:
                        next_issue = issues[0]
                    else:
                        next_issue = issues[(index + 1)]
            self.display.issue_preview = next_issue

        else:
            self.display.current_screen = 'issue_selection'
            self.display.issue_preview = self.display.issue

        self.update_display()

    def left_button(self):
        issues = self.issues[::-1]
        self.navigate_next_issue(issues)

    def right_button(self):
        issues = self.issues[:]
        self.navigate_next_issue(issues)

    def action_button(self):
        if self.display.current_screen == 'issue_selection':
            if self.display.issue_preview:
                self.display.issue = self.display.issue_preview
                self.display.start_time = datetime.now()
                self.display.current_screen = "issue"
                self.update_display_every(0.85)
            else:
                self.timers.remove_by_tag("display_update")
                self.update_display()

        elif self.display.current_screen == "issue":
            self.refresh_issues()
            # Start a task
            if self.display.issue.fields.status.id != self.api.in_progress_status:
                self.api.start_issue(self.display.issue)
                self.display.start_time = datetime.now()

            # Stop a task
            else:
                if self.waiting_ack:
                    self.display.register_time()
                    self.waiting_ack = False
                    self.display.blinking = False
                else:
                    self.api.change_status(self.display.issue, self.api.todo_status)
                    self.display.register_time()
                    self.timers.remove_by_tag("display_update")
            self.refresh_issues()
            self.update_display_every(0.85)

    def update_display_every(self, seconds):
        next_job_time = datetime.now() + timedelta(seconds=seconds)
        self.timers.remove_by_tag("display_update")
        self.timers.add(next_job_time,
                        lambda: self.update_display_every(seconds),
                        "display_update")
        self.update_display()

    def update_display(self):
        self.display.update()
        if self.display._image:
            self.serial.write(b'I')
            image_bytes = bytearray()
            bit_position = 0
            binary = ''
            for pixel in self.display._image.getdata():
                bit_position += 1
                binary += str(int(pixel > 0))
                if bit_position == 8:
                    self.serial.write(bytes([int(binary, 2)]))
                    bit_position = 0
                    binary = ''

    def read_serial(self):
        message = self.serial.read_until().strip().decode()
        if message:
            print(message)

        # filter message noises
        if self.last_message[0] == message:
            if (datetime.now() - self.last_message[1]).total_seconds() < 0.2:
                # ignore if the same message is received within 0.2 seconds
                return
        self.last_message = (message, datetime.now())

        if message == "prev":
            self.left_button()
        elif message == "next":
            self.right_button()

        elif message == "start":
            self.action_button()

        elif message == "reset":
            self.start()

    def main_loop_iteration(self):
        self.read_serial()
        self.timers.execute()

    def exit(self):
        info_log("Shutting down")
        self.display.register_time()
        self.serial.close()

    def run(self):
        self.start()
        atexit.register(self.exit)
        while True:
            self.main_loop_iteration()
            delay = (1 / self.clock) - (datetime.now() - self._last_iteration).total_seconds()
            delay = delay if delay >= 0 else 1 / self.clock
            sleep(delay)


