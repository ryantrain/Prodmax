const organization_id = sessionStorage.getItem("organization_id");
const organization_members_ids = JSON.parse(sessionStorage.getItem("preFetchedData_organization_taskboard")).organization_members_usernames.map(member => member.user_id);
const organization_members_names = JSON.parse(sessionStorage.getItem('preFetchedData_organization_taskboard')).organization_members_usernames.map(member => member.username);
const taskboardData = sessionStorage.getItem('preFetchedData_organization_taskboard');

function loadOrganizationTaskboards() {
    const orglist = document.getElementById('task-list');
    const organization_name = sessionStorage.getItem('organization_name');
    const organization_title_element = document.querySelector('.organization_taskboard_header_title');
    
    const organization_title = document.createElement('h2');
    organization_title.textContent = organization_name;
    organization_title_element.appendChild(organization_title);

    if (taskboardData) {
        const data = JSON.parse(taskboardData);
        for (const task of data.tasks) {
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

    // sessionStorage.removeItem('preFetchedData_organization_taskboard');
    sessionStorage.removeItem('organization_id');
    sessionStorage.removeItem('organization_name');
}

function loadOrganizationMembers() {
    const data = JSON.parse(taskboardData);
    const organization_member_list = document.getElementById('organization_members_list');
    organization_members_names.forEach((member, index) => {
        const memberElement = document.createElement('div');
        memberElement.classList.add('organization_members_list_item');
        memberElement.dataset.member_id = organization_members_ids[index];

            const memberName = document.createElement('span');
            memberName.classList.add('organization_members_list_item_username');
            memberName.textContent = member;

        memberElement.appendChild(memberName);

        if (data.organization[0].owner === organization_members_ids[index]) {
            const ownerBadge = document.createElement('div');
            ownerBadge.classList.add('organization_members_list_item_owner_badge');
                const ownerText = document.createElement('a');
                ownerText.textContent = 'Owner';
                ownerBadge.appendChild(ownerText);
            memberElement.appendChild(ownerBadge);
            organization_member_list.prepend(memberElement);
            return;
        }

        organization_member_list.appendChild(memberElement);
    });
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
    } catch (error) {
        console.error('Error occurred while adding task to taskboard:', error);
    }
}

function addOrganizationTaskboardCard(task_title, task_description, taskboard_id) {
    const taskList = document.getElementById('task-list');

    const taskElement = document.createElement('div');
    taskElement.classList.add('task-card');
    taskElement.classList.add('organization-card-incomplete');
    taskElement.dataset.taskboard_id = taskboard_id;

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

    
        // Create task options button
        const taskOptions = document.createElement('button');
        taskOptions.classList.add('organization-card-options-button');
        taskOptions.textContent = '...';
        taskOptions.onclick = (e) => {
            e.stopPropagation();
            // Handle task options click (e.g., show a dropdown menu with options)
            toggleOrganizationCardOptionsDropdown(taskElement);
        }
        
    taskElement.appendChild(taskOptions);
    taskElement.appendChild(taskName);
    taskElement.appendChild(taskContent);

    const createTaskButton = document.querySelector('.create-task-button');
    
    const memberAssignment = document.createElement('button');
    memberAssignment.classList.add('assign-members-button');
    memberAssignment.textContent = 'Assign';
    memberAssignment.onclick = async (e) => {
        e.stopPropagation();
        
        const confirmButton = document.getElementById('assign_members_confirm_button');
        confirmButton.dataset.taskboardId = taskboard_id;

        toggleAssignMembersOverlay();
        await loadAssignMembersList(taskboard_id);
    }
    
    taskElement.appendChild(memberAssignment);

    taskList.insertBefore(taskElement, createTaskButton);
    taskElement.onclick = async () => {
        await fetchTaskInfo(taskboard_id);
    }    
}

document.getElementById('assign_members_confirm_button').addEventListener('click', async (e) => {
    const currentTaskboardId = e.currentTarget.dataset.taskboardId;
    
    if (!currentTaskboardId) {
        console.error("No active taskboard ID found on the confirm button!");
        return;
    }

    toggleAssignMembersOverlay();
    await updateAssignedMembers(currentTaskboardId);
});

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

function toggleEditTaskboardInterface(card) {
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

async function editTaskboard(taskboard_id) {
    // Function updates the corresponding task to the db and updates the text on the card
    const task_title = document.getElementById('task_title_input_edit').value;
    const task_description = document.getElementById('task_description_input_edit').value;

    const formData = new FormData();
    formData.append('new_taskboard_name', task_title);
    formData.append('new_taskboard_description', task_description);

    try {
        response = await fetch(`http://localhost:8000/api/organizations/${organization_id}/${taskboard_id}/edit_organization_taskboard`, {
            method: 'POST',
            body: formData
        });

    } catch (error) {
        console.error('Error editing task:', error);
    }
}

async function deleteTask(taskboard_id) {
    try {
        const response = await fetch(`http://localhost:8000/api/organizations/${organization_id}/${taskboard_id}/delete_organization_taskboard`                                              , {
            method: 'POST'
        });
    } catch (error) {
        console.error('Error deleting task:', error);
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

function toggleInviteMembersOverlay() {
    const overlay = document.getElementById('invite_members_overlay');
    const container = document.getElementById('invite_members_container');
    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

function loadInviteMembersList(taskboard_id) {
    if (!document.getElementById('invite_members_overlay').classList.contains('active') || !document.getElementById('invite_members_container').classList.contains('active')) {
        return;
    }

    const inviteMembersList = document.getElementById('invite_members_list');
    const friends = document.querySelectorAll('.friends_item');

    // clear existing items
    while (inviteMembersList.firstChild) {
        inviteMembersList.removeChild(inviteMembersList.firstChild);
    }

    for (const friend of friends) {
        if (!organization_members_ids.includes(friend.dataset.friend_id)) {
            const invite_members_list_item = document.createElement('div');
            invite_members_list_item.classList.add('invite_members_list_item');

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.classList.add('invite_members_list_item_checkbox');
                invite_members_list_item.appendChild(checkbox);

                const textContent = document.createElement('span');
                textContent.classList.add('invite_members_list_item_username');
                textContent.textContent = friend.textContent;
                invite_members_list_item.appendChild(textContent);

            invite_members_list_item.dataset.friend_id = friend.dataset.friend_id;
            
            inviteMembersList.appendChild(invite_members_list_item);
        }
    }
    document.getElementById('invite_members_selected_count_link').textContent = document.querySelectorAll('.invite_members_list_item_checkbox:checked').length + ' Selected';
}

async function InviteSelectedMembers() {
    const selectedMembers = document.querySelectorAll('.invite_members_list_item_checkbox:checked');
    const selectedMemberIds = Array.from(selectedMembers).map(member => member.parentElement.dataset.friend_id);

    try {
        const formData = new FormData();
        selectedMemberIds.forEach(id => formData.append('member_ids', id));

        response = await fetch(`http://localhost:8000/api/organizations/${organization_id}/invite_members`, {
            method: 'POST',
            body: formData
        });

    } catch (error) {
        console.error('Error inviting members:', error);
    }
}

function toggleOrganizationMembersPane() {
    document.getElementById('organization_members_container').classList.toggle('active');
    document.querySelector('.main-container').classList.toggle('organization-members-open')
}

async function loadAssignMembersList(taskboard_id) {
    try {
        response = await fetch(`http://localhost:8000/api/taskboard/${taskboard_id}/retrieve_members`, {
            method: 'GET'
        });

        if (response.ok){
            data = await response.json();
        }

        const taskboard_member_ids = data.data.data[0].members;

        if (!document.getElementById('assign_members_overlay').classList.contains('active') || !document.getElementById('assign_members_container').classList.contains('active')) {
            return;
        }

        const assignMembersList = document.getElementById('assign_members_list');

        // clear existing items
        while (assignMembersList.firstChild) {
            assignMembersList.removeChild(assignMembersList.firstChild);
        }

        for (let i = 0; i < organization_members_ids.length; i++){
            const member = organization_members_names[i];
            const user_id = organization_members_ids[i];
            const assign_members_list_item = document.createElement('div');
            assign_members_list_item.classList.add('assign_members_list_item');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('assign_members_list_item_checkbox');

            if (taskboard_member_ids.includes(user_id)) {
                checkbox.checked = true;
            }

            assign_members_list_item.appendChild(checkbox);
            const textContent = document.createElement('span');
            textContent.classList.add('assign_members_list_item_username');
            textContent.textContent = member;
            assign_members_list_item.appendChild(textContent);

            assign_members_list_item.dataset.username = member;
            assign_members_list_item.dataset.user_id = user_id;
            assignMembersList.appendChild(assign_members_list_item);
        }
        document.getElementById('assign_members_selected_count_link').textContent = document.querySelectorAll('.assign_members_list_item_checkbox:checked').length + ' Selected';
    } catch (error) {
        console.error('Error retrieving members:', error);
    }
}

function toggleAssignMembersOverlay(){
    const overlay = document.getElementById('assign_members_overlay');
    const container = document.getElementById('assign_members_container');
    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

async function updateAssignedMembers(taskboard_id) {
    const selectedMembers = document.querySelectorAll('.assign_members_list_item_checkbox:checked');
    
    const selectedMemberIds = Array.from(selectedMembers).map(member => member.parentElement.dataset.user_id);

    console.log(selectedMemberIds);
    console.log(taskboard_id);

    try {
        const formData = new FormData();
        selectedMemberIds.forEach(id => formData.append('member_ids', id));

        response = await fetch(`http://localhost:8000/api/taskboard/${taskboard_id}/assign_members`, {
            method: 'POST',
            body: formData
        });

    } catch (error) {
        console.error('Error assigning members:', error);
    }
}

function toggleOrganizationCardOptionsDropdown(card) {
    const orglist = document.getElementById('task-list');
    // Check if dropdown already exists somewhere
    const check_dropdown = orglist.querySelectorAll('.organization-card-options-dropdown');
    if (check_dropdown.length > 0) {
        if (check_dropdown[0].parentElement === card) {
            check_dropdown[0].remove();
            return;
        }
        check_dropdown.forEach(dropdown => dropdown.remove());
    }

    // Create dropdown menu
    const dropdown = document.createElement('div');
    dropdown.classList.add('organization-card-options-dropdown');

        // Add options to dropdown
        const editOption = document.createElement('div');
            editOption.classList.add('organization-card-options-dropdown-item');
            editOption.textContent = 'Edit';
            editOption.onclick = (e) => {
                // Handle edit option click
                e.stopPropagation();
                dropdown.remove();
                current_editing_task = card
                toggleEditTaskboardInterface(card);
            };
        dropdown.appendChild(editOption);

        const deleteOption = document.createElement('div');
            deleteOption.classList.add('organization-card-options-dropdown-item');
            deleteOption.textContent = 'Delete';
            deleteOption.onclick = (e) => {
                e.stopPropagation();
                deleteTask(card.dataset.taskboard_id); 
                dropdown.remove();
            };
        dropdown.appendChild(deleteOption);

    card.appendChild(dropdown);
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
    await editTaskboard(current_editing_task.dataset.taskboard_id);
    current_editing_task = null; // Reset current editing task after edit
    toggleEditTaskOverlay();
});

document.getElementById('invite_members_button').addEventListener('click', () => {
    toggleInviteMembersOverlay();
    loadInviteMembersList();
});

document.getElementById('invite_members_overlay').addEventListener('click', (event) => {
    if (event.target === document.getElementById('invite_members_overlay')) {
        toggleInviteMembersOverlay();
    }
});

document.getElementById('invite_members_list').addEventListener('click', (event) => {
    if (event.target.classList.contains('invite_members_list_item')) {
        event.target.querySelector('.invite_members_list_item_checkbox').checked = !event.target.querySelector('.invite_members_list_item_checkbox').checked;
    } else if (event.target.classList.contains('invite_members_list_item_username')) {
        event.target.closest('.invite_members_list_item').querySelector('.invite_members_list_item_checkbox').checked = !event.target.closest('.invite_members_list_item').querySelector('.invite_members_list_item_checkbox').checked;
    }
    document.getElementById('invite_members_selected_count_link').textContent = document.querySelectorAll('.invite_members_list_item_checkbox:checked').length + ' Selected';
});

document.getElementById('invite_members_search_query_input').addEventListener('input', () => {
    const searchQuery = document.getElementById('invite_members_search_query_input').value.toLowerCase();
    const inviteMembersListNames = document.querySelectorAll('.invite_members_list_item_username');

    inviteMembersListNames.forEach(item => {
        const username = item.textContent.toLowerCase();
        if (username.includes(searchQuery)) {
            item.parentElement.classList.remove('hidden');
        } else {
            item.parentElement.classList.add('hidden');
        }
    });
});

document.getElementById('invite_members_cancel_button').addEventListener('click', () => {
    toggleInviteMembersOverlay();
});

document.getElementById('invite_members_confirm_button').addEventListener('click', async () => {
    await InviteSelectedMembers();
    toggleInviteMembersOverlay();
});

document.getElementById('organization_taskboard_header_members_button').addEventListener('click', () => {
    toggleOrganizationMembersPane();
});

document.getElementById('organization_members_close_button').addEventListener('click', () => {
    toggleOrganizationMembersPane();
});

document.getElementById('assign_members_list').addEventListener('click', (event) => {
    if (event.target.classList.contains('assign_members_list_item')) {
        event.target.querySelector('.assign_members_list_item_checkbox').checked = !event.target.querySelector('.assign_members_list_item_checkbox').checked;
    } else if (event.target.classList.contains('assign_members_list_item_username')) {
        event.target.closest('.assign_members_list_item').querySelector('.assign_members_list_item_checkbox').checked = !event.target.closest('.assign_members_list_item').querySelector('.assign_members_list_item_checkbox').checked;
    }
    document.getElementById('assign_members_selected_count_link').textContent = document.querySelectorAll('.assign_members_list_item_checkbox:checked').length + ' Selected';
});

document.getElementById('assign_members_cancel_button').addEventListener('click', () => {
    toggleAssignMembersOverlay();
});

document.getElementById('assign_members_overlay').addEventListener('click', (event) => {
    if (event.target === document.getElementById('assign_members_overlay')) {
        toggleAssignMembersOverlay();
    }
});


// Order matters
loadOrganizationMembers();
loadOrganizationTaskboards();