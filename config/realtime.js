const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    await supabase.auth.getUser();

    const channel = supabase.channel('message_updates')
                .on('postgres_changes', { 
                    event: "INSERT", 
                    schema: "public", 
                    table: "messages", 
                }, async (payload) => {
                    const activeChannel = document.querySelector('.channel_item.active_channel');
                    const message_channel_ID = payload.new.chat_id;

                    if (activeChannel && activeChannel.dataset.channel_id === message_channel_ID) {
                        const messageSection = document.getElementById('messages_section');
                        const p = document.createElement('p');
                        p.classList.add('message_item');
                        p.textContent = await getUsername(payload.new.sender_user_id) + ': ' + payload.new.content;
                        messageSection.appendChild(p);
                        messageSection.scrollTop = messageSection.scrollHeight;
                    }

                    if (!activeChannel || activeChannel.dataset.channel_id !== message_channel_ID) {
                        const channelButtons = document.querySelectorAll('.channel_item');
                        channelButtons.forEach(button => {
                            if (button.dataset.channel_id === message_channel_ID) {
                                if (!button.textContent.endsWith(' *')) {
                                    button.textContent = button.textContent + ' *';
                                }
                            }
                        });
                    }
                }).subscribe();
}

async function getUsername(sender_id) {
    try{
        const response = await fetch(`http://localhost:8000/api/user/${sender_id}`, {
            method: 'POST'
        });

        const data = await response.json();

        return data.username;

    } catch (error) {
        console.error('Error fetching username for sender ID:', sender_id, error);
        return 'Unknown User';
    }
}

initializeRealtime().catch(error => {
    console.error('Error initializing realtime:', error);
});