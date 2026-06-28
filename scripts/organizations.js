var organization_id = null;
var current_editing_organization = null;
var current_deleting_organization = null;
const organizations = document.querySelectorAll('.organization-card');

async function loadOrganizations() {
    const orglist = document.getElementById('organization-list');

    try {
        fetchedOrganizationData = sessionStorage.getItem('preFetchedOrganizations');
        
        organizationData = JSON.parse(fetchedOrganizationData);

        organizationData.organizations.forEach(organization => {
            addOrganizationCard(organization.organization_id, organization.name, organization.description)
        });
    } catch (error) {
        console.error('Error occurred while loading organizations:', error);
    }

    const createOrganizationButton = document.createElement('button');
    createOrganizationButton.textContent = '+';
    createOrganizationButton.classList.add('create-organization-button');
    createOrganizationButton.onclick = () => {
        toggleAddOrganizationOverlay();
    };
    orglist.appendChild(createOrganizationButton);
}

// get the new organization info and make an http post request to add the organization, then draw the card if successful
async function createOrganization(event) {
    event.preventDefault();
    try {
        organization_title = document.getElementById('organization_title_input').value;
        organization_description = document.getElementById('organization_description_input').value;

        formData = new FormData();

        formData.append('organization_name', organization_title);
        formData.append('organization_description', organization_description);
        const response = await fetch('http://localhost:8000/api/organizations/add_organization', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            data = await response.json();
            addOrganizationCard(data.data[0].organization_id_returned, organization_title, organization_description);

        }

    } catch (error) {
        console.error('Error occurred while adding new organization:', error);
    }
}

function addInvitationCard(organization_id, organization_title) {
    const organization = document.getElementById('organization-list');

    const organizationElement = document.createElement('div');
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

    organization.insertBefore(organizationElement, organization.lastElementChild);

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

// toggle the add organization button???
function toggleAddOrganizationOverlay() {
    const overlay = document.querySelector('.add_organization_overlay');
    const container = document.getElementById('add_organization_container');

    if (container.classList.contains('active')) {
        document.getElementById('organization_title_input').value = '';
        document.getElementById('organization_description_input').value = '';
    }

    overlay.classList.toggle('active');
    container.classList.toggle('active');
}

// toggle the edit organization button???
function toggleEditOrganizationOverlay() {
    const overlay = document.querySelector('.add_organization_overlay');
    const container = document.getElementById('edit_organization_container');
    if (container.classList.contains('active')) {
        overlay.addEventListener('transitionend', () => {
            document.getElementById('organization_title_input_edit').value = '';
        document.getElementById('organization_description_input_edit').value = '';
        }, {once: true});
    }
    overlay.classList.toggle('active');
    container.classList.toggle('active');
}


function toggleEditOrganizationInterface(card) {
    const overlay = document.querySelector('.add_organization_overlay');
    const container = document.getElementById('edit_organization_container');

    overlay.classList.toggle('active');
    container.classList.toggle('active');

    // Pre-fill the edit form with the current organization details
    const currentTitle = card.querySelector('.card-title').textContent;
    const currentDescription = card.querySelector('.card-description-text').textContent;

    document.getElementById('organization_title_input_edit').value = currentTitle;
    document.getElementById('organization_description_input_edit').value = currentDescription;
}

// async function EditOrganization() {
//     // Function updates the corresponding organization to the db and updates the text on the card
//     const organization_title = document.getElementById('organization_title_input_edit').value;
//     const organization_description = document.getElementById('organization_description_input_edit').value;

//     const formData = new FormData();
//     formData.append('organization_name', organization_title);
//     formData.append('organization_description', organization_description);

//     try {
//         response = await fetch('http://localhost:8000/api/organizationboard/edit_organization' ,{
//             method: 'POST',
//             body: formData
//         });

//         if (response.ok) {
//             current_editing_organization.querySelector('.card-title').querySelector('h3').textContent = organization_title;
//             current_editing_organization.querySelector('.card-description-text').textContent = organization_description;
//         }

//     } catch (error) {
//         console.error('Error editing organization:', error);
//     }
// }

// async function deleteOrganization(organization_id) {
//     try {
//         const response = await fetch('http://localhost:8000/api/organizationboard/' + taskboard_id + '/delete_organization/' + organization_id, {
//             method: 'POST'
//         });

//         if (response.ok) {
//             current_deleting_organization.remove();
//             current_deleting_organization = null;
//         }
//     } catch (error) {
//         console.error('Error deleting organization:', error);
//     }
// }

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

        if (organization_taskboard_data){
            sessionStorage.setItem('preFetchedData_organization_taskboard', JSON.stringify(organization_taskboard_data));
            sessionStorage.setItem('organization_id', organization_id);
            sessionStorage.setItem('organization_name', organization_name);
            sessionStorage.setItem('preFetchedData_navbar', JSON.stringify(navbar_data));
            sessionStorage.setItem('private', "False");
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

document.querySelector('.add_organization_overlay').addEventListener('click', () => {
    if (document.getElementById('add_organization_container').classList.contains('active')) {
        toggleAddOrganizationOverlay();
    } else if (document.getElementById('edit_organization_container').classList.contains('active')) {
        toggleEditOrganizationOverlay();
}});

document.getElementById('close_add_organization_button').addEventListener('click', toggleAddOrganizationOverlay);

document.getElementById('submit_organization_button').addEventListener('click', (e) => {
    createOrganization(e);
    toggleAddOrganizationOverlay();
});

document.getElementById('close_edit_organization_button').addEventListener('click', () => {
    toggleEditOrganizationOverlay();
});

document.getElementById('confirm_edit_organization_button').addEventListener('click', async () => {
    await EditOrganization(current_editing_organization.dataset.organization_id);
    current_editing_organization = null; // Reset current editing organization after edit
    toggleEditOrganizationOverlay();
});

loadOrganizations();