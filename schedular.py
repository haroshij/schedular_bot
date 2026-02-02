import heapq
from datetime import datetime
from task import Task


class Scheduler:
    def __init__(self):
        self.tasks_heap = []

    def add_task(self, task: Task):
        heapq.heappush(self.tasks_heap, (task.scheduled_time, -task.priority, task))

    def get_next_task(self):
        if not self.tasks_heap:
            return None
        return self.tasks_heap[0][2]

    def pop_next_task(self):
        if not self.tasks_heap:
            return None
        return heapq.heappop(self.tasks_heap)[2]

    def check_due_tasks(self):
        """Возвращает все задачи, которые пора выполнить"""
        now = datetime.now()
        due_tasks = []
        while self.tasks_heap and self.tasks_heap[0][0] <= now:
            _, _, task = heapq.heappop(self.tasks_heap)
            due_tasks.append(task)
        return due_tasks
