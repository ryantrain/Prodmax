const { supabase } = require('../config/supabaseClient');

async function initializeRealtime() {
    const { data: { session } } = await supabase.auth.getSession();
    const data_user = await supabase.auth.getUser();
    const user = data_user.data.user;
    const user_id = user.id;

    const organization_invitations_channel = supabase.channel('organization_invitations_updates')
        .on('postgres_changes', {
            event: "INSERT",
            schema: "public",
            table: "organization_invitations",
            }, async (payload) => {
            try {
                const organization_id = payload.new.organization_id;

                const response = await fetch(`http://localhost:8000/api/organizations/${organization_id}/retrieve_name`, {
                    method: 'GET'
                });
                if (response.ok) {
                    const data = await response.json();
                    const organization_name = data.data[0];

                    addInvitationCard(organization_id, organization_name);
                }
            } catch (error) {
                console.error('Error fetching organization name:', error);
            }
            
        }).subscribe();
}

function addInvitationCard(organization_id, organization_title) {
    const organization = document.getElementById('organization-list');

    const organizationElement = document.createElement('div');
    console.log(organization_id, organization_title);
    organizationElement.dataset.organization_id = organization_id;
    organizationElement.classList.add('organization_invitation_card');

    const organization_title_element = document.createElement('h3');
    organization_title_element.textContent = organization_title;
    organization_title_element.classList.add('organization_invitation_card_title');
    organizationElement.appendChild(organization_title_element);

    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('organization_invitation_card_button_container');
        acceptButton = document.createElement('button');
        acceptButton.textContent = 'Accept';
        acceptButton.classList.add('organization_invitation_card_accept_button');

        acceptButton.onclick = async () => {
            await acceptInvitation(organization_id);
        };

        declineButton = document.createElement('button');
        declineButton.textContent = 'Decline';
        declineButton.classList.add('organization_invitation_card_decline_button');

        declineButton.onclick = () => {
            const response_decline_invitation = declineInvitation(organization_id);

            // Remove the invitation card from the DOM
            if (response_decline_invitation) {
                organizationElement.remove();
            }
        };

    buttonContainer.appendChild(acceptButton);
    buttonContainer.appendChild(declineButton);
    organizationElement.appendChild(buttonContainer);

    organization.insertBefore(organizationElement, organization.firstElementChild);

}

//draws the organization cards
function addOrganizationCard(organization_id, organization_title, organization_description) {
    const organization = document.getElementById('organization-list');

    const organizationElement = document.createElement('div');
    organizationElement.dataset.organization_id = organization_id;
    organizationElement.classList.add('organization-card');

        // Create organization name/title element
        const organizationName = document.createElement('div')
        organizationName.classList.add('card-title');
            const organizationTitle = document.createElement('h3')
            organizationTitle.textContent = organization_title;
        organizationName.appendChild(organizationTitle);

        // Create organization content element
        const organizationContent = document.createElement('div');
        organizationContent.classList.add('card-description-container');
            const organizationText = document.createElement('p');
            organizationText.classList.add('card-description-text')
            organizationText.textContent = organization_description;
        organizationContent.appendChild(organizationText);

    organizationElement.appendChild(organizationName);
    organizationElement.appendChild(organizationContent);

    const createOrganizationButton = document.querySelector('.create-organization-button');

    organization.insertBefore(organizationElement, createOrganizationButton);
    organizationElement.onclick = async () => {
        await fetchOrganizationTasks(organization_id, organization_title);
    }
}

async function fetchOrganizationTasks(organization_id, organization_name) {
    try {
        const organization_response = await fetch(`http://localhost:8000/api/${organization_id}/organization_taskboard`, {
            method: 'GET'
        });

        const navbar_response = await fetch('http://localhost:8000/api/navbar', {
            method: 'GET'
        });

        const navbar_data = await navbar_response.json();
        const organization_taskboard_data = await organization_response.json();

        if(organization_taskboard_data){
            sessionStorage.setItem('preFetchedData_organization_taskboard', JSON.stringify(organization_taskboard_data));
            sessionStorage.setItem('organization_id', organization_id);
            sessionStorage.setItem('organization_name', organization_name);
            sessionStorage.setItem('preFetchedData_navbar', JSON.stringify(navbar_data));
        } else {
            console.log("No data to fetch");
        }

        window.location.href = 'organization_taskboard.html';

    } catch (error) {
        console.error(`Error fetching taskboard data for ID ${organization_id}:`, error);
        return { organizations: [] };
    }
}

async function acceptInvitation(organization_id) {
    try {
        response = await fetch ("http://localhost:8000/api/organizations/" + organization_id + "/accept_invitation" , {
            method: 'POST'
        });

        if (response.ok) {
            // Remove the invitation card from the DOM
            const invitationCard = document.querySelector(`.organization_invitation_card[data-organization_id="${organization_id}"]`);
            const data = await response.json()
            if (invitationCard) {
                invitationCard.remove();
            }
            if (data.data){
                addOrganizationCard(data.data.organization_id, data.data.name, data.data.description);
            }
        }
    } catch (error) {
        console.error('Error accepting invitation:', error);
    }
}

function declineInvitation(organization_id) {
    try {
        response = fetch ("http://localhost:8000/api/organizations/" + organization_id + "/decline_invitation" , {
            method: 'POST'
        });
        return true;
    } catch (error) {
        console.error('Error declining invitation:', error);
    }
}

initializeRealtime();