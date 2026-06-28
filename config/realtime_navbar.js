const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    const { data: { session } } = await supabase.auth.getSession();
    const data_user = await supabase.auth.getUser();
    const user = data_user.data.user;
    const user_id = user.id;

    const message_channel = supabase.channel('message_updates')
                .on('postgres_changes', { 
                    event: "INSERT", 
                    schema: "public", 
                    table: "messages",
                }, async (payload) => {
                    const activeChannel = document.querySelector('.channel_item.active_channel');
                    const message_channel_ID = payload.new.chat_id;

                    if (activeChannel && activeChannel.parentElement.dataset.channel_id === message_channel_ID) {
                        const messageSection = document.getElementById('messages_section');
                        const p = document.createElement('p');
                        p.classList.add('message_item');
                        p.textContent = await getUsername(payload.new.sender_user_id) + ': ' + payload.new.content;
                        messageSection.appendChild(p);
                        messageSection.scrollTop = messageSection.scrollHeight;
                    }

                    if (!activeChannel || activeChannel.parentElement.dataset.channel_id !== message_channel_ID) {
                        const channelButtons = document.querySelectorAll('.channel_item');
                        channelButtons.forEach(button => {
                            if (button.parentElement.dataset.channel_id === message_channel_ID) {
                                if (!button.textContent.endsWith(' *')) {
                                    button.textContent = button.textContent + ' *';
                                }
                            }
                        });
                    }
                }).subscribe();

    const channel_channel = supabase.channel('channel_updates')
                .on('postgres_changes', { 
                    event: "INSERT",
                    schema: "public", 
                    table: "channel_list", 
                }, async (payload) => {
                    const channel_id = payload.new.channel_id;
                    const channel_name = payload.new.channel_name;
                    const channel_list = document.getElementById('channel_list');

                    if (channel_name) {
                        channel_list.insertAdjacentHTML('beforeend', 
                            `<div class="channel_wrapper" data-channel_id="${channel_id}">
                                <input type="checkbox" class="channel_select_checkbox hidden">
                                <button class="channel_item">${channel_name}</button>
                            </div>`
                        );
                    }
                }).subscribe();
    
    const receive_friend_requests_channel = supabase.channel('friend_request_updates')
                .on('postgres_changes', { 
                    event: "INSERT",
                    schema: "public", 
                    table: "friendships",
                    filter: "sender_id=neq." + user_id
                }, async (payload) => {
                    const friend_request_list = document.getElementById('friend_requests_list');
                    const sender_id = payload.new.sender_id;
                    const sender_username = await getUsername(sender_id);
                    friend_request_list.insertAdjacentHTML('beforeend',
                        `<div class="friend_request_item">
                            <p>${sender_username}</p>
                            <div class="friend_request_buttons_section">
                                <button id="accept_friend_request_button" data-user_id="${sender_id}" data-username="${sender_username}" class="friend_request_button">✓</button>
                                <button id="reject_friend_request_button" data-user_id="${sender_id}" data-username="${sender_username}" class="friend_request_button">✗</button>
                            </div>
                        </div>`)
                }).subscribe();

    const friend_request_accepted_channel = supabase.channel('friend_request_accepted_updates')
                .on('postgres_changes', { 
                    event: "UPDATE",
                    schema: "public",
                    table: "friendships",
                    filter: "status=eq.accepted"
                }, async (payload) => {
                    console.log(payload);
                    const friendList = document.getElementById('friends_sidebar');
                    let friend_id = "";
                    if (payload.new.uuid_pair[0] === user_id) {
                        friend_id = payload.new.uuid_pair[1];
                    } else if (payload.new.uuid_pair[1] === user_id) {
                        friend_id = payload.new.uuid_pair[0];
                    }

                    const friend_username = await getUsername(friend_id);
                    friendList.insertAdjacentHTML('beforeend', `<p class="friends_item" data-user_id="${friend_id}">${friend_username}</p>`);
                    const formData = new FormData();
                    formData.append('friend_id', friend_id);
                }).subscribe();
}

async function getUsername(sender_id) {
    try{
        const response = await fetch(`http://localhost:8000/api/user/${sender_id}`, {
            method: 'GET'
        });

        const data = await response.json();

        return data.username;

    } catch (error) {
        console.error('Error fetching username for sender ID:', sender_id, error);
        return 'Unknown User';
    }
}

async function get_username_for_groupchat(channel_id) {
    try {
        const response = await fetch(`http://localhost:8000/api/channel/${channel_id}`, {
            method: 'GET'
        });
    } catch (error) {
        console.error('Error fetching channel name for channel ID:', channel_id, error);
        return 'Unknown Channel';
    }
};

async function logout() {
    try {
        const response = await fetch('http://localhost:8000/api/logout', {
            method: 'GET'
        });

        if (response.ok) {
            supabase.auth.signOut();
            window.location.href = 'login.html';
        }

    } catch (error) {
        console.error('Error logging out:', error);
    }
}

initializeRealtime().catch(error => {
    console.error('Error initializing realtime:', error);
});

document.getElementById('logout_link').addEventListener('click', async () => {
    await logout();
});