var taskboard_id = null;

function loadTaskboard() {
    const taskboardData = sessionStorage.getItem('preFetchedData_private_taskboard');
    taskboard_id = sessionStorage.getItem('taskboard_id');
    const orglist = document.getElementById('organization-list');

    if (taskboardData) {
        const data = JSON.parse(taskboardData);

        for (const task of data.tasks) {
            const taskElement = document.createElement('div');
            taskElement.classList.add('organization-card');

                // Create task name/title element
                const taskName = document.createElement('div')
                taskName.classList.add('card-title');
                    const taskTitle = document.createElement('h3')
                    taskTitle.textContent = task.task_name;
                taskName.appendChild(taskTitle);

                // Create task content element
                const taskContent = document.createElement('div');
                taskContent.classList.add('card-description-container');
                    const taskText = document.createElement('p');
                    taskText.classList.add('card-description-text')
                    taskText.textContent = task.task_description;
                taskContent.appendChild(taskText);

            taskElement.appendChild(taskName);
            taskElement.appendChild(taskContent);

            orglist.appendChild(taskElement);

        }

    const createTaskButton = document.createElement('button');
    createTaskButton.textContent = '+';
    createTaskButton.classList.add('create-task-button');
    createTaskButton.onclick = () => {
        toggleAddTaskOverlay();
    };
    orglist.appendChild(createTaskButton);

        sessionStorage.removeItem('preFetchedData_private_taskboard');
    }
}

async function addTask(taskboard_id) {
    try {
        task_title = document.getElementById('task_title_input').value;
        task_description = document.getElementById('task_description_input').value;

        formData = new FormData();

        formData.append('task_name', task_title);
        formData.append('task_description', task_description);
        const response = await fetch('http://localhost:8000/api/taskboard/' + taskboard_id + '/add_personal_task', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            addTaskCard(task_title, task_description);
        }

    } catch (error) {
        console.error('Error occurred while adding task to taskboard:', error);
    }
}

function addTaskCard(task_title, task_description) {
    const orglist = document.getElementById('organization-list');

    const taskElement = document.createElement('div');
    taskElement.classList.add('organization-card');

        // Create task name/title element
        const taskName = document.createElement('div')
        taskName.classList.add('card-title');
            const taskTitle = document.createElement('h3')
            taskTitle.textContent = task_title;
        taskName.appendChild(taskTitle);

        // Create task content element
        const taskContent = document.createElement('div');
        taskContent.classList.add('card-description-container');
            const taskText = document.createElement('p');
            taskText.classList.add('card-description-text')
            taskText.textContent = task_description;
        taskContent.appendChild(taskText);

    taskElement.appendChild(taskName);
    taskElement.appendChild(taskContent);

    const createTaskButton = document.querySelector('.create-task-button');
    orglist.insertBefore(taskElement, createTaskButton);
}

function toggleAddTaskOverlay() {
    const overlay = document.querySelector('.add_task_overlay');
    const container = document.querySelector('.add_task_container');

    if (container.classList.contains('active')) {
        document.getElementById('task_title_input').value = '';
        document.getElementById('task_description_input').value = '';
    }

    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

document.querySelector('.add_task_overlay').addEventListener('click', toggleAddTaskOverlay);
document.getElementById('close_add_task_button').addEventListener('click', toggleAddTaskOverlay);
document.getElementById('submit_task_button').addEventListener('click', () => {
    addTask(taskboard_id);
    toggleAddTaskOverlay();
});

loadTaskboard();
