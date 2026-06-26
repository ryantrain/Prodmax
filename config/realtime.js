const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    await supabase.auth.getUser();

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
                    console.log(payload)

                    if (channel_name) {
                        channel_list.insertAdjacentHTML('beforeend', 
                            `<div class="channel_wrapper" data-channel_id="${channel_id}">
                                <input type="checkbox" class="channel_select_checkbox hidden">
                                <button class="channel_item">${channel_name}</button>
                            </div>`
                        );
                    }
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

initializeRealtime().catch(error => {
    console.error('Error initializing realtime:', error);
});