from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import re
import json
from task_parser import TaskParser

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize the task parser
parser = TaskParser()

# In-memory storage (use database in production)
tasks = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/parse-task', methods=['POST'])
def parse_task():
    """Parse task text and return structured data"""
    try:
        data = request.get_json()
        task_text = data.get('text', '').strip()
        
        if not task_text:
            return jsonify({'error': 'No task text provided'}), 400
        
        # Use TensorFlow-based parser
        parsed_task = parser.parse(task_text)
        
        return jsonify({
            'success': True,
            'parsed': parsed_task
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    return jsonify({'tasks': tasks})

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    try:
        data = request.get_json()
        
        task = {
            'id': len(tasks) + 1,
            'title': data.get('title'),
            'date': data.get('date'),
            'time': data.get('time'),
            'original_text': data.get('original_text'),
            'created_at': datetime.now().isoformat(),
            'completed': False
        }
        
        tasks.append(task)
        
        return jsonify({
            'success': True,
            'task': task
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion status"""
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            return jsonify({'success': True, 'task': task})
    
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
    