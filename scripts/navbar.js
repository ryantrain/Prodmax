async function fetchData() {
    try {
        const rawData = sessionStorage.getItem('preFetchedData');

        if (rawData) {
            const data = JSON.parse(rawData);

            const list = document.getElementById('channel_list');
            list.innerHTML = data.channels[1].map((name, index) => `<button onclick="display_messages_pane(this)" data-channel_id="${data.channels[0][index]}" class="channel_item">${name}</button>`).join('');

            const friendList = document.getElementById('friends_sidebar');
            friendList.innerHTML += data.friends.map(name => `<p class="friends_item">${name}</p>`).join('');

            const friendRequestList = document.getElementById('friend_requests_list');
            friendRequestList.innerHTML += data.friend_requests.map(name => 
                `<div class="friend_request_item">
                    <p>${name}</p>
                    <div class="friend_request_buttons_section">
                        <button id="accept_friend_request_button" data-username="${name}" onclick="acceptFriendRequest(this)" class="friend_request_button">✓</button>
                        <button id="reject_friend_request_button" data-username="${name}" onclick="rejectFriendRequest(this)" class="friend_request_button">✗</button>
                    </div>
                </div>`).join('');

            sessionStorage.removeItem('preFetchedData');
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function display_messages_pane(button) {
    document.getElementById('message_pane').classList.add('show_message_pane');
    load_messages(button.dataset.channel_id);
    button.classList.add('active_channel');
}

async function load_messages(channel_id) {
    const response = await fetch('http://localhost:8000/api/load_messages/' + channel_id, {
        method: 'POST'
    });

    const data = await response.json();

    const messages = data.messages || [];

    const messageSection = document.getElementById('messages_section');
    messageSection.innerHTML = messages.toReversed().map(message => `<p class="message_item">${message}</p>`).join('');
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
    document.getElementById('message_pane').classList.toggle('open_message_pane');
    document.getElementById('message_pane').classList.remove('show_message_pane');

    document.getElementById('message_pane').addEventListener('transitionend', () => {
        setTimeout(() => {
            document.querySelectorAll('.message_item').forEach(item => item.remove());
        }, 100);
    });
    
    const activeButton = document.querySelector('.channel_item.active_channel');
    if (activeButton) {
        activeButton.classList.remove('active_channel');
    }
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("show");
}

function toggleChannelList() {
    document.querySelector(".main-container").classList.toggle("channel-open");
    document.getElementById("channel_list").classList.toggle("open_channel_list");
    if (document.getElementById("message_pane").classList.contains("show_message_pane")) {
        document.getElementById("message_pane").classList.remove("open_message_pane");
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

            document.getElementById('friends_sidebar').innerHTML += `<p class="friends_item">${username}</p>`;

            document.getElementById('channel_list').innerHTML += `<button onclick="display_messages_pane(this)" data-channel_id="${data.data.channel_id}" class="channel_item">${username}</button>`;
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

// Updates the message history with the new message
document.getElementById('message_input_form').addEventListener('submit', async(e) => {
    e.preventDefault();
    const messageInput = e.target.elements['message_input'];

    const channel_id = document.querySelector('.channel_item.active_channel').dataset.channel_id;
    const message = messageInput.value;

    if (message === '') {
        return;
    }

    const response = await send_message(channel_id, message);
    messageInput.value = '';

    document.getElementById('messages_section').innerHTML += `<p class="message_item">${response.message}</p>`;
    const messageSection = document.getElementById('messages_section');
    messageSection.scrollTop = messageSection.scrollHeight;
});

document.getElementById('add_friends_input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === 'Return') {
        sendFriendRequest();
    }
});

fetchData();