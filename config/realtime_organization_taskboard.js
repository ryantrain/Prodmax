const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    const { data: { session } } = await supabase.auth.getSession();
    const data_user = await supabase.auth.getUser();
    const user = data_user.data.user;
    const user_id = user.id;

    const new_taskboard_channel = supabase.channel('new_taskboard_updates')
                .on('postgres_changes', { 
                    event: "INSERT", 
                    schema: "public", 
                    table: "taskboards",
                    filter: `organization_id=eq.${organization_id}`
                }, async (payload) => {
                    const taskboard_id = payload.new.uuid;
                    const taskboard_name = payload.new.taskboard_name;
                    const taskboard_description = payload.new.taskboard_description;

                    addOrganizationTaskboardCard(taskboard_name, taskboard_description, taskboard_id);
                }).subscribe();

    const new_member_channel = supabase.channel('new_member_updates')
                .on('postgres_changes', { 
                    event: "UPDATE", 
                    schema: "public", 
                    table: "organizations",
                    filter: `organization_id=eq.${organization_id}`
                }, async (payload) => {
                    const new_column = payload.new.members;
                    const old_column = []
                    
                    document.querySelectorAll('.organization_members_list_item').forEach(item => {
                        old_column.push(item.dataset.member_id);
                    });

                    if (old_column.every(member => new_column.includes(member))) {
                        const new_members = new_column.filter(member => !old_column.includes(member));
                        const formData = new FormData();
                        formData.append('user_ids', [new_members]);

                        try {
                            const response = await fetch('http://localhost:8000/api/users/retrieve_usernames', {
                                method: 'POST',
                                body: formData
                            });

                            if (response.ok) {
                                const data = await response.json();
                                const member_list = document.getElementById('organization_members_list');
                                member_list.insertAdjacentHTML('beforeend',
                                    `<div class="organization_members_list_item">
                                        <span class="organization_members_list_item_username">${data.data[0]}</span>
                                    </div>`)
                            }
                        } catch (error) {
                            console.error('Error occurred while fetching new member username:', error);
                        }
                    }
                }).subscribe();

    const delete_taskboard_channel = supabase.channel('delete_taskboard_updates')
                .on('postgres_changes', { 
                    event: "DELETE",
                    schema: "public",
                    table: "taskboards",
                }, async (payload) => {
                    const taskboard_id = payload.old.uuid;
                    const taskboard_card = document.querySelector(`[data-taskboard_id="${taskboard_id}"]`);
                    if (taskboard_card) {
                        taskboard_card.remove();
                    }
                }).subscribe();

    const edit_taskboard_channel = supabase.channel('edit_taskboard_updates')
                .on('postgres_changes', { 
                    event: "UPDATE", 
                    schema: "public", 
                    table: "taskboards",
                }, async (payload) => {
                    const taskboard_name = payload.new.taskboard_name;
                    const taskboard_description = payload.new.taskboard_description;

                    current_editing_task.querySelector('.card-title').querySelector('h3').textContent = taskboard_name;
                    current_editing_task.querySelector('.card-description-text').textContent = taskboard_description;
                    current_editing_task = null; // Reset current editing task after edit
                }).subscribe();
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

initializeRealtime();