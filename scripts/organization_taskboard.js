const organization_id = sessionStorage.getItem("organization_id");

function loadOrganizationTaskboards() {
    const taskboardData = sessionStorage.getItem('preFetchedData_organization_taskboard'); 
    const orglist = document.getElementById('task-list');

    if (taskboardData) {
        const data = JSON.parse(taskboardData);
        console.log(data);
        for (const task of data.organizations) {
            addOrganizationTaskboardCard(task.taskboard_name, task.taskboard_description, task.uuid)
        }
    }
    const createTaskButton = document.createElement('button');
    createTaskButton.textContent = '+';
    createTaskButton.classList.add('create-task-button');
    createTaskButton.onclick = () => {
        toggleAddTaskOverlay();        
    };
    orglist.appendChild(createTaskButton);

    sessionStorage.removeItem('preFetchedData_organization_taskboard');
}

async function createOrganizationTaskboard(organization_id) {
    try {
        taskboard_title = document.getElementById('task_title_input').value;
        taskboard_description = document.getElementById('task_description_input').value;

        formData = new FormData();

        formData.append('taskboard_name', taskboard_title);
        formData.append('taskboard_description', taskboard_description);
        const response = await fetch(`http://localhost:8000/api/taskboard/${organization_id}/add_organization_taskboard`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            data = await response.json();
            console.log(data);
            addOrganizationTaskboardCard(taskboard_title, taskboard_description, data.data.data[0].uuid);
        }

    } catch (error) {
        console.error('Error occurred while adding task to taskboard:', error);
    }
}

function addOrganizationTaskboardCard(task_title, task_description, taskboard_id) {
    const task = document.getElementById('task-list');

    const taskElement = document.createElement('div');
    taskElement.classList.add('task-card');
    taskElement.classList.add('organization-card-incomplete');

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
    task.insertBefore(taskElement, createTaskButton);
    taskElement.onclick = async () => {
        await fetchTaskInfo(taskboard_id);
    }
}

function toggleAddTaskOverlay() {
    const overlay = document.querySelector('.add_task_overlay');
    const container = document.getElementById('add_task_container');

    if (container.classList.contains('active')) {
        document.getElementById('task_title_input').value = '';
        document.getElementById('task_description_input').value = '';
    }

    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

function toggleEditTaskOverlay() {
    const overlay = document.querySelector('.add_task_overlay');
    const container = document.getElementById('edit_task_container');
    if (container.classList.contains('active')) {
        overlay.addEventListener('transitionend', () => {
            document.getElementById('task_title_input_edit').value = '';
        document.getElementById('task_description_input_edit').value = '';
        }, {once: true});
    }
    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

function ToggleCardOptionsDropdown(card) {
    const orglist = document.getElementById('task-list');
    // Check if dropdown already exists somewhere
    const check_dropdown = orglist.querySelectorAll('.card-options-dropdown');
    if (check_dropdown.length > 0) {
        if (check_dropdown[0].parentElement === card) {
            check_dropdown[0].remove();
            return;
        }
        check_dropdown.forEach(dropdown => dropdown.remove());
    }

    // Create dropdown menu
    const dropdown = document.createElement('div');
    dropdown.classList.add('card-options-dropdown');

        // Add options to dropdown
        const editOption = document.createElement('div');
            editOption.classList.add('card-options-dropdown-item');
            editOption.textContent = 'Edit';
            editOption.onclick = () => {
                // Handle edit option click 
                dropdown.remove();
                current_editing_task = card
                toggleEditTaskInterface(card);
            };
        dropdown.appendChild(editOption);

        const deleteOption = document.createElement('div');
            deleteOption.classList.add('card-options-dropdown-item');
            deleteOption.textContent = 'Delete';
            deleteOption.onclick = () => {
                current_deleting_task = card;
                deleteTask(card.dataset.task_id); 
                dropdown.remove();
            };
        dropdown.appendChild(deleteOption);

    card.appendChild(dropdown);
}

function toggleEditTaskInterface(card) {
    const overlay = document.querySelector('.add_task_overlay');
    const container = document.getElementById('edit_task_container');

    overlay.classList.toggle('active');
    container.classList.toggle('active');

    // Pre-fill the edit form with the current task details
    const currentTitle = card.querySelector('.card-title').textContent;
    const currentDescription = card.querySelector('.card-description-text').textContent;

    document.getElementById('task_title_input_edit').value = currentTitle;
    document.getElementById('task_description_input_edit').value = currentDescription;
}

async function EditTask(task_id) {
    // Function updates the corresponding task to the db and updates the text on the card
    const task_title = document.getElementById('task_title_input_edit').value;
    const task_description = document.getElementById('task_description_input_edit').value;

    const formData = new FormData();
    formData.append('task_name', task_title);
    formData.append('task_description', task_description);

    try {
        response = await fetch('http://localhost:8000/api/taskboard/' + taskboard_id + '/edit_task/' + task_id, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            current_editing_task.querySelector('.card-title').querySelector('h3').textContent = task_title;
            current_editing_task.querySelector('.card-description-text').textContent = task_description;
        }

    } catch (error) {
        console.error('Error editing task:', error);
    }
}

async function deleteTask(task_id) {
    try {
        const response = await fetch('http://localhost:8000/api/taskboard/' + taskboard_id + '/delete_task/' + task_id, {
            method: 'POST'
        });

        if (response.ok) {
            current_deleting_task.remove();
            current_deleting_task = null;
        }
    } catch (error) {
        console.error('Error deleting task:', error);
    }
}

document.querySelector('.add_task_overlay').addEventListener('click', () => {
    if (document.getElementById('add_task_container').classList.contains('active')) {
        toggleAddTaskOverlay();
    } else if (document.getElementById('edit_task_container').classList.contains('active')) {
        toggleEditTaskOverlay();
}});

document.getElementById('close_add_task_button').addEventListener('click', toggleAddTaskOverlay);

document.getElementById('submit_task_button').addEventListener('click', () => {
    createOrganizationTaskboard(organization_id);
    toggleAddTaskOverlay();
});

document.getElementById('close_edit_task_button').addEventListener('click', () => {
    toggleEditTaskOverlay();
});

document.getElementById('confirm_edit_task_button').addEventListener('click', async () => {
    await EditTask(current_editing_task.dataset.task_id);
    current_editing_task = null; // Reset current editing task after edit
    toggleEditTaskOverlay();
});

loadOrganizationTaskboards();

async function fetchTaskInfo(taskboard_id) {
    try {
        const taskboard_response = await fetch(`http://localhost:8000/api/taskboard/${taskboard_id}`, {
            method: 'GET'
        });

        const navbar_response = await fetch('http://localhost:8000/api/navbar', {
            method: 'GET'
        });

        const taskboard_data = await taskboard_response.json();
        const navbar_data = await navbar_response.json();

        sessionStorage.setItem('preFetchedData_private_taskboard', JSON.stringify(taskboard_data));
        sessionStorage.setItem('preFetchedData_navbar', JSON.stringify(navbar_data));
        sessionStorage.setItem('taskboard_id', taskboard_id);

        window.location.href = 'my_taskboard.html';

    } catch (error) {
        console.error(`Error fetching taskboard data for ID ${taskboard_id}:`, error);
        return { taskboards: [] };
    }
}