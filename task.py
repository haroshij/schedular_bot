from datetime import datetime, timedelta
from uuid import uuid4


class Task:
    def __init__(self, title, user_id, scheduled_time, priority=1, repeat_interval=None):
        self.id = str(uuid4())
        self.title = title
        self.user_id = user_id
        self.scheduled_time = scheduled_time
        self.priority = priority
        self.repeat_interval = repeat_interval
        self.completed = False

    def postpone(self, delta: timedelta):
        self.scheduled_time += delta

    def mark_complete(self):
        self.completed = True
        if self.repeat_interval:
            self.scheduled_time += self.repeat_interval
            self.completed = False
