async function fetchData() {
    try {
        const rawData = sessionStorage.getItem('preFetchedData_navbar');

        if (rawData) {
            const data = JSON.parse(rawData);

            const channel_list = document.getElementById('channel_list');
            const channel_list_HTML = data.channels[1].map((name, index) => 
                `<div class="channel_wrapper" data-channel_id="${data.channels[0][index]}" data-channel_type="${data.channels[2][index]}">
                    <input type="checkbox" class="channel_select_checkbox hidden">
                    <button class="channel_item">${name}</button>
                </div>`).join('');
            channel_list.insertAdjacentHTML('beforeend', channel_list_HTML);

            const friendList = document.getElementById('friends_sidebar');
            const friendsListHTML = data.friends[0].map((name, index) => `<p class="friends_item" data-friend_id = "${data.friends[1][index]}">${name}</p>`).join('');
            friendList.insertAdjacentHTML('beforeend', friendsListHTML);

            const friendRequestList = document.getElementById('friend_requests_list');
            const friendRequestList_HTML = data.friend_requests.map(name => 
                `<div class="friend_request_item">
                    <p>${name}</p>
                    <div class="friend_request_buttons_section">
                        <button id="accept_friend_request_button" data-username="${name}" class="friend_request_button">✓</button>
                        <button id="reject_friend_request_button" data-username="${name}" class="friend_request_button">✗</button>
                    </div>
                </div>`).join('');
            friendRequestList.insertAdjacentHTML('beforeend', friendRequestList_HTML);

            sessionStorage.removeItem('preFetchedData_navbar');
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function display_messages_pane(button) {
    document.getElementById('message_pane').classList.add('show_message_pane');
    document.getElementById('message_pane').classList.add('open_message_pane_on_toggle');
    load_messages(button.parentElement.dataset.channel_id);
    button.classList.add('active_channel');
}

async function load_messages(channel_id) {
    const response = await fetch('http://localhost:8000/api/load_messages/' + channel_id, {
        method: 'GET'
    });

    const data = await response.json();

    const messages = data.messages || [];

    const messageSection = document.getElementById('messages_section');
    while (messageSection.firstChild) {
        messageSection.removeChild(messageSection.firstChild);
    }
    messageSection.insertAdjacentHTML('beforeend', messages.toReversed().map(message => `<p class="message_item">${message}</p>`).join(''));
    messageSection.scrollTop = messageSection.scrollHeight;
}

async function send_message(channel_id, message) {
    const formData = new FormData();
    formData.append('channel_id', channel_id);
    formData.append('content', message);
    const response = await fetch('http://localhost:8000/api/send_message', {
        method: 'POST',
        body: formData,
        });
    
    return await response.json();
}

function closeMessagePane() {
    const messagePane = document.getElementById('message_pane');

    messagePane.classList.toggle('open_message_pane_on_toggle');
    messagePane.classList.remove('show_message_pane');
    
    const activeButton = document.querySelector('.channel_item.active_channel');
    if (activeButton) {
        activeButton.classList.remove('active_channel');
    }

    document.querySelectorAll('.message_item').forEach(item => item.remove());
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("show");
}

function toggleChannelList() {
    document.querySelector(".main-container").classList.toggle("channel-open");
    document.getElementById("channel_list").classList.toggle("open_channel_list");
    if (document.getElementById("message_pane").classList.contains("show_message_pane")) {
        document.getElementById("message_pane").classList.toggle("open_message_pane_on_toggle");
    }
}

function toggleFriendRequests() {
    document.querySelector(".main-container").classList.toggle("friends_open");
    document.getElementById("friends_overlay").classList.toggle("friends_open");
    document.getElementById("friends_sidebar").classList.toggle("friends_open");
}

function sendFriendRequest() {
    const query = document.getElementById('add_friends_input').value;

    if (query === '') {
        return;
    }

    document.getElementById('add_friends_input').value = '';

    const formData = new FormData();
    formData.append('query', query);

    try {
        fetch('http://localhost:8000/api/add_friend', {
            method: 'POST',
            body: formData
        });
    } catch (error) {
        console.error('Error sending friend request:', error);
    }
}
function toggleFriendRequestPane() {
    document.getElementById('friend_requests_pane').classList.toggle('open');
}

function closeFriendRequestPane() {
    document.getElementById('friend_requests_pane').classList.remove('open');
}

async function acceptFriendRequest(button) {
    const username = button.dataset.username;
    const formData = new FormData();

    formData.append('addressee_username', username);

    try {
        const response = await fetch('http://localhost:8000/api/accept_friend_request', {
            method: 'POST',
            body: formData
        });

        if (response.ok){
            const data = await response.json();
            button.parentElement.parentElement.remove();

            document.getElementById('friends_sidebar').insertAdjacentHTML('beforeend', `<p class="friends_item">${username}</p>`);

            document.getElementById('channel_list').insertAdjacentHTML('beforeend', `<div class="channel_wrapper" data-channel_id="${data.data.channel_id}">
                <input type="checkbox" class="channel_select_checkbox hidden">
                <button class="channel_item">${username}</button>
            </div>`);
        }

    } catch (error) {
        console.error('Error accepting friend request:', error);
    }
};

function rejectFriendRequest(button) {
    const username = button.dataset.username;
    const formData = new FormData();
    
    formData.append('addressee_username', username);

    try {
        fetch('http://localhost:8000/api/decline_friend_request', {
            method: 'POST',
            body: formData
        });
    } catch (error) {
        console.error('Error rejecting friend request:', error);
    }

    button.parentElement.parentElement.remove();
}

async function renderDashboard() {
    try {
        const dashboard_response = await fetch('http://localhost:8000/api/dashboard', {
            method: 'GET'
        });

        const navbar_response = await fetch('http://localhost:8000/api/navbar', {
            method: 'GET'
        });

        const dashboardData = await dashboard_response.json();
        const navbarData = await navbar_response.json();

        sessionStorage.setItem('preFetchedData_navbar', JSON.stringify(navbarData));
        sessionStorage.setItem('preFetchedData_dashboard', JSON.stringify(dashboardData));
    } catch (error) {
        console.error('Error rendering dashboard:', error);
    }

    window.location.href = 'dashboard.html';
}

function toggleChannelCreation() {
    const list = document.getElementById('channel_list');
    const checkboxes = document.querySelectorAll('.channel_select_checkbox');
    const channelItems = document.querySelectorAll('.channel_item');
    
    list.classList.toggle('channel_creation_mode'); 
    document.getElementById('create_channel_button').classList.toggle('hidden');
    document.getElementById('channel_creation_title').classList.toggle('hidden');
    document.getElementById('selected_channels_counter').classList.toggle('hidden');
    document.getElementById('create_group_channel_search_channel_query').classList.toggle('hidden');

    checkboxes.forEach(cb => cb.classList.toggle('hidden'));
    
    if (!list.classList.contains('channel_creation_mode')) {
        checkboxes.forEach(cb => cb.checked = false);
        document.querySelectorAll('.channel_item').forEach(item => {
            if (item.parentElement.classList.contains('hidden')) {
                item.parentElement.classList.remove('hidden');
            }
        })
    } else {
        document.querySelectorAll('.channel_item').forEach(item => {
            console.log(item.parentElement.dataset.channel_type);
            if (item.parentElement.dataset.channel_type != 'private') {
                item.parentElement.classList.add('hidden');
            }
        })
    }
}

async function renderOrganizations() {
    try {
        const navbar_response = await fetch('http://localhost:8000/api/navbar', {
            method: 'GET'
        });

        const navbarData = await navbar_response.json();

        sessionStorage.setItem('preFetchedData_navbar', JSON.stringify(navbarData));
    } catch (error) {
        console.error('Error rendering organizations:', error);
    }

    window.location.href = 'organizations.html';
}

async function createGroupChannel() {
    const selectedChannels = Array.from(document.querySelectorAll('.channel_select_checkbox:checked'))
    // const channelName = document.getElementById('new_channel_name_input').value ???
    const selectedFriendNames = selectedChannels.map(cb => cb.nextElementSibling.textContent);

    if (selectedChannels.length > 0) {
        const formData = new FormData();
        selectedFriendNames.forEach(name => formData.append('selected_friend_names', name));

        try {
            response = await fetch('http://localhost:8000/api/channel/create_group_channel', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                data = await response.json();
                const channel_id = data.data.channel_id;
                const channel_list = document.getElementById('channel_list');
                channel_list.insertAdjacentHTML('beforeend', 
                    `<div class="channel_wrapper" data-channel_id="${data.data.channel_id}">
                        <input type="checkbox" class="channel_select_checkbox">
                        <button class="channel_item">${selectedFriendNames.join(', ')}</button>
                    </div>`
                );
            }
        } catch (error) {
            console.error('Error creating group channel:', error);
        }
    }
}

// Updates the message history with the new message
document.getElementById('message_input_form').addEventListener('submit', async(e) => {
    e.preventDefault();
    const messageInput = e.target.elements['message_input'];

    const channel_id = document.querySelector('.channel_item.active_channel').parentElement.dataset.channel_id;
    const message = messageInput.value;

    if (message === '') {
        return;
    }

    const response = await send_message(channel_id, message);
    messageInput.value = '';
});

document.getElementById('add_friends_input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === 'Return') {
        sendFriendRequest();
    }
});

document.getElementById('channel_list').addEventListener('click', (event) => {
    const selectedCounter = document.getElementById('selected_channels_counter');
    
    if (document.getElementById('channel_list').childElementCount <= 2) {
        return;
    }

    if (document.getElementById('channel_list').classList.contains('channel_creation_mode')) {
        if (event.target.classList.contains('channel_select_checkbox')) {
            selectedCounter.textContent = `${document.querySelectorAll('.channel_select_checkbox:checked').length} Selected`;
            return; 
        }
        
        if (event.target.classList.contains('channel_item')) {
            event.preventDefault();
            const checkbox = event.target.previousElementSibling;
            if (checkbox && checkbox.classList.contains('channel_select_checkbox')) {
                checkbox.checked = !checkbox.checked;                
                selectedCounter.textContent = `${document.querySelectorAll('.channel_select_checkbox:checked').length} Selected`;
            }
            return;
        } else if (event.target.classList.contains('channel_wrapper')) {
            event.preventDefault();
            event.target.querySelector('.channel_select_checkbox').checked = !event.target.querySelector('.channel_select_checkbox').checked;
            selectedCounter.textContent = `${document.querySelectorAll('.channel_select_checkbox:checked').length} Selected`;
            return;
        }
    }

    if (!document.getElementById('channel_list').classList.contains('channel_creation_mode') && event.target.innerText.endsWith(' *')) {
        event.target.innerText = event.target.innerText.slice(0, -2);
    }

    if (!document.getElementById('channel_list').classList.contains('channel_creation_mode') && event.target.classList.contains('channel_item')) {
        display_messages_pane(event.target);
    }
});

document.getElementById('friend_requests_list').addEventListener('click', (event) => {
    event.preventDefault();
    if (event.target.id === 'accept_friend_request_button') {
        acceptFriendRequest(event.target);
    } else if (event.target.id === 'reject_friend_request_button') {
        rejectFriendRequest(event.target);
    }
});

document.getElementById('menu-btn').addEventListener('click', toggleSidebar);
document.getElementById('friends_toggle').addEventListener('click', toggleFriendRequests);
document.getElementById('channel_list_toggle').addEventListener('click', toggleChannelList);
document.getElementById('home_link').addEventListener('click', renderDashboard);
document.getElementById('overlay').addEventListener('click', toggleSidebar);
document.getElementById('friends_overlay').addEventListener('click', toggleFriendRequests);
document.querySelector('#add_friends_button').addEventListener('click', toggleFriendRequestPane);
document.getElementById('friend_requests_pane_back').addEventListener('click', closeFriendRequestPane);
document.getElementById('add_friends_submit').addEventListener('click', sendFriendRequest);
document.getElementById('message_pane_toggler').addEventListener('click', closeMessagePane);
document.getElementById('create_channel_button').addEventListener('click', async () => {
    await createGroupChannel();
    document.getElementById('selected_channels_counter').textContent = '0 Selected';
    toggleChannelCreation();
});

document.getElementById('organizations_link').addEventListener('click', () => {
    renderOrganizations();
});

document.getElementById('workspaces_link').addEventListener('click', () => {
    window.location.href = 'workspaces.html';
});

document.getElementById('settings_link').addEventListener('click', () => {
    window.location.href = 'settings.html';
});

document.getElementById('toggle_channel_creation_button').addEventListener('click', () => {
    toggleChannelCreation();
});

document.getElementById('create_group_channel_search_channel_query').addEventListener('input', (event) => {
    const query = event.target.value.toLowerCase();
    const channelItems = document.querySelectorAll('.channel_item');

    channelItems.forEach(item => {
        const channelName = item.textContent.toLowerCase();
        const channelWrapper = item.parentElement;

        if (channelName.includes(query) && channelWrapper.dataset.channel_type === 'private') {
            channelWrapper.classList.remove('hidden');
        } else {
            channelWrapper.classList.add('hidden');
        }
    });
});

document.getElementById('friends_sidebar_search_query_input').addEventListener('input', (event) => {
    const query = event.target.value.toLowerCase();
    const friendItems = document.querySelectorAll('.friends_item');

    friendItems.forEach(item => {
        const friendName = item.textContent.toLowerCase();

        if (friendName.includes(query)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }

    });
});

fetchData();