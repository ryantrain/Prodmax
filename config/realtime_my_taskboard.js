const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    const organization_taskboard_channel = supabase.channel('organization_taskboard_updates')
        .on('postgres_changes', {
            event: "INSERT",
            schema: "public",
            table: "tasks",
            filter: `parent_taskboard=eq.${taskboard_id}`
        }, (payload) => {
            const task_id = payload.new.id;
            const task_title = payload.new.task_name;
            const task_description = payload.new.task_description;

            addSubtaskCard(task_title, task_description, task_id);              
        }).subscribe();

    const task_edit_channel = supabase.channel('task_edit_updates')
        .on('postgres_changes', {
            event: "UPDATE",
            schema: "public",
            table: "tasks",
            filter: `parent_taskboard=eq.${taskboard_id}`
        }, (payload) => {
            const task_id = payload.new.id;
            const card = document.querySelector(`[data-task_id="${task_id}"]`);

            if (card.dataset.task_complete === 'true' && payload.new.completed === false) {
                card.classList.remove('organization-card-completed');
                card.classList.add('organization-card-incomplete');
            } else if (card.dataset.task_complete === 'false' && payload.new.completed === true) {
                card.classList.remove('organization-card-incomplete');
                card.classList.add('organization-card-completed');
            }
            
            card.dataset.task_complete = payload.new.completed;

            card.querySelector('.card-title').firstElementChild.textContent = payload.new.task_name;
            card.querySelector('.card-description-container').firstElementChild.textContent = payload.new.task_description;

        }).subscribe();

    const task_delete_channel = supabase.channel('task_delete_updates')
        .on('postgres_changes', {
            event: "DELETE",
            schema: "public",
            table: "tasks",
            filter: `parent_taskboard=eq.${taskboard_id}`
        }, (payload) => {
            const task_id = payload.old.id;
            const card = document.querySelector(`[data-task_id="${task_id}"]`);
            if (card) {
                card.remove();
            }
        }).subscribe();
}

function addSubtaskCard(task_title, task_description, task_id) {
    const task = document.getElementById('task-list');

    const taskElement = document.createElement('div');
    taskElement.dataset.task_complete = 'false';
    taskElement.classList.add('organization-card-incomplete');
    taskElement.dataset.task_id = task_id;

        // Create mark complete button
        const markCompleteButton = document.createElement('button');
        markCompleteButton.classList.add('mark-complete-button');
        markCompleteButton.textContent = "✓";
        markCompleteButton.onclick = async () => {
            const response = await fetch('http://localhost:8000/api/taskboard/' + taskboard_id + '/toggle_task_completed/' + task_id, {
                method: 'POST'
            });

            if (response.ok) {
                taskElement.dataset.task_complete = taskElement.dataset.task_complete === 'true' ? 'false' : 'true';
                if (taskElement.dataset.task_complete === 'true') {
                    taskElement.classList.remove('organization-card-incomplete');
                    taskElement.classList.add('organization-card-completed');
                } else {
                    taskElement.classList.remove('organization-card-completed');
                    taskElement.classList.add('organization-card-incomplete');
                }
            }
        }
        taskElement.appendChild(markCompleteButton);

        // Create task options button
        const taskOptions = document.createElement('button');
        taskOptions.classList.add('card-options-button');
        taskOptions.textContent = '...';
        taskOptions.onclick = (e) => {
            e.stopPropagation();
            // Handle task options click (e.g., show a dropdown menu with options)
            toggleCardOptionsDropdown(taskElement);

        }
        taskElement.appendChild(taskOptions);

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
}

function toggleCardOptionsDropdown(card) {
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

initializeRealtime();