from flask import Flask, jsonify, request
from celery import Celery
import time

app = Flask(__name__)
celery = Celery(app.name, broker='your_broker_url')

@celery.task(bind=True)
def long_running_task(self):
    for i in range(10):
        time.sleep(10)  # Simulating a long task
        self.update_state(state='PROGRESS', meta={'current': i, 'total': 10})
    return {'current': 10, 'total': 10, 'status': 'Task completed!'}

@app.route('/start_task', methods=['POST'])
def start_task():
    task = long_running_task.apply_async()
    return jsonify({"task_id": task.id})

@app.route('/task_status/<task_id>')
def task_status(task_id):
    task = long_running_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'current': task.info.get('current', 0), 'total': task.info.get('total', 1), 'status': task.info.get('status', '')}
    else:
        response = {'state': task.state, 'status': str(task.info)}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
