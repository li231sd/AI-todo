class AITodoApp {
    constructor() {
        this.tasks = [];
        this.initializeEventListeners();
        this.loadTasks();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTask();
        });

        // Input change for AI preview
        document.getElementById('taskInput').addEventListener('input', (e) => {
            this.showAIPreview(e.target.value);
        });

        // Example items click
        document.querySelectorAll('.example-item').forEach(item => {
            item.addEventListener('click', () => {
                const exampleText = item.dataset.text;
                document.getElementById('taskInput').value = exampleText;
                this.showAIPreview(exampleText);
            });
        });
    }

    async showAIPreview(text) {
        const preview = document.getElementById('aiPreview');
        const previewText = document.getElementById('aiPreviewText');

        if (!text || text.length < 3) {
            preview.classList.add('d-none');
            return;
        }

        try {
            const response = await fetch('/api/parse-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            if (data.success && data.parsed) {
                const parsed = data.parsed;
                let previewHTML = `<strong>${parsed.title}</strong>`;
                
                if (parsed.date) {
                    previewHTML += ` <span class="badge bg-success">${parsed.date}</span>`;
                }
                
                if (parsed.time) {
                    previewHTML += ` <span class="badge bg-info">${parsed.time}</span>`;
                }

                if (parsed.confidence) {
                    const confidencePercent = Math.round(parsed.confidence * 100);
                    previewHTML += ` <small class="text-muted">(${confidencePercent}% confidence)</small>`;
                }

                previewText.innerHTML = previewHTML;
                preview.classList.remove('d-none');
            } else {
                preview.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error parsing task:', error);
            preview.classList.add('d-none');
        }
    }

    async addTask() {
        const taskInput = document.getElementById('taskInput');
        const text = taskInput.value.trim();
        
        if (!text) {
            this.showAlert('Please enter a task', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            // First, parse the task
            const parseResponse = await fetch('/api/parse-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const parseData = await parseResponse.json();

            if (!parseData.success) {
                throw new Error(parseData.error || 'Failed to parse task');
            }

            // Then, add the task
            const addResponse = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: parseData.parsed.title,
                    date: parseData.parsed.date,
                    time: parseData.parsed.time,
                    original_text: text
                })
            });

            const addData = await addResponse.json();

            if (addData.success) {
                taskInput.value = '';
                document.getElementById('aiPreview').classList.add('d-none');
                this.loadTasks();
                this.showAlert('Task added successfully!', 'success');
            } else {
                throw new Error(addData.error || 'Failed to add task');
            }

        } catch (error) {
            console.error('Error adding task:', error);
            this.showAlert('Error adding task: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            const data = await response.json();
            
            if (data.tasks) {
                this.tasks = data.tasks;
                this.renderTasks();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
            this.showAlert('Error loading tasks', 'danger');
        }
    }

    renderTasks() {
        const container = document.getElementById('tasksContainer');
        const emptyState = document.getElementById('emptyState');

        if (emptyState) emptyState.style.display = 'none';

        if (this.tasks.length === 0) {
            if (emptyState) {
                emptyState.style.display = 'block';
                container.innerHTML = '';
                container.appendChild(emptyState);
            } else {
                container.innerHTML = '<div class="text-center py-4 text-muted">No tasks yet. Add your first one above.</div>';
            }
            return;
        }

        const tasksHTML = this.tasks.map(task => this.createTaskHTML(task)).join('');
        container.innerHTML = tasksHTML;

        // Add event listeners to task buttons
        this.addTaskEventListeners();
    }

    createTaskHTML(task) {
        const completedClass = task.completed ? 'completed' : '';
        const checkIcon = task.completed ? 'fas fa-check-circle' : 'far fa-circle';
        
        return `
            <div class="task-item ${completedClass}" data-task-id="${task.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="task-title">${this.escapeHtml(task.title)}</h6>
                        
                        <div class="task-meta">
                            ${task.date ? `<span class="task-badge badge-date"><i class="fas fa-calendar me-1"></i>${task.date}</span>` : ''}
                            ${task.time ? `<span class="task-badge badge-time"><i class="fas fa-clock me-1"></i>${task.time}</span>` : ''}
                        </div>
                        
                        <div class="task-original">
                            <i class="fas fa-quote-left me-1"></i>
                            "${this.escapeHtml(task.original_text)}"
                        </div>
                    </div>
                    
                    <div class="btn-group btn-group-sm ms-3" role="group">
                        <button type="button" class="btn btn-outline-success toggle-btn" data-task-id="${task.id}">
                            <i class="${checkIcon}"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-btn" data-task-id="${task.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    addTaskEventListeners() {
        // Toggle completion
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskId = parseInt(e.currentTarget.dataset.taskId);
                await this.toggleTask(taskId);
            });
        });

        // Delete task
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const taskId = parseInt(e.currentTarget.dataset.taskId);
                if (confirm('Are you sure you want to delete this task?')) {
                    await this.deleteTask(taskId);
                }
            });
        });
    }

    async toggleTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/toggle`, {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                this.loadTasks();
            } else {
                throw new Error(data.error || 'Failed to toggle task');
            }
        } catch (error) {
            console.error('Error toggling task:', error);
            this.showAlert('Error updating task', 'danger');
        }
    }

    async deleteTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.loadTasks();
                this.showAlert('Task deleted successfully!', 'success');
            } else {
                throw new Error(data.error || 'Failed to delete task');
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showAlert('Error deleting task', 'danger');
        }
    }

    updateStats() {
        const total = this.tasks.length;
        const completed = this.tasks.filter(task => task.completed).length;
        const pending = total - completed;

        document.getElementById('taskCount').textContent = total;
        document.getElementById('totalTasks').textContent = total;
        document.getElementById('completedTasks').textContent = completed;
        document.getElementById('pendingTasks').textContent = pending;
    }

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (show) {
            loadingIndicator.classList.remove('d-none');
        } else {
            loadingIndicator.classList.add('d-none');
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to document
        document.body.appendChild(alertDiv);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AITodoApp();
});
