function loadTaskboard() {
    const taskboardData = sessionStorage.getItem('preFetchedData_my_taskboard');

    if (taskboardData) {
        const data = JSON.parse(taskboardData);
        const orglist = document.getElementById('organization-list');

        for (const task of data.tasks) {
            const taskElement = document.createElement('div');
            taskElement.classList.add('organization-card');

                // Create task name/title element
                const taskName = document.createElement('div')
                taskName.classList.add('card-title');
                    const taskTitle = document.createElement('h3')
                    taskTitle.textContent = task.task_name;
                taskName.appendChild(taskTitle);

                // Create task content element
                const taskContent = document.createElement('div');
                taskContent.classList.add('card-description-container');
                    const taskText = document.createElement('p');
                    taskText.classList.add('card-description-text')
                    taskText.textContent = task.task_description;
                taskContent.appendChild(taskText);

            taskElement.appendChild(taskName);
            taskElement.appendChild(taskContent);

            orglist.appendChild(taskElement);

        }

        sessionStorage.removeItem('preFetchedData_my_taskboard');
    }
}

loadTaskboard();
