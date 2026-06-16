const createTaskButton = document.getElementById("create_button");
const modalOverlay = document.getElementById("modal-overlay");
const cancelTaskButton = document.getElementById("cancel-button");
const addButton = document.getElementById("add-button");
const taskInput = document.getElementById("task-input");
const taskList = document.getElementById("task-list");
const emptyText = document.getElementById("emptyState")

createTaskButton.addEventListener("click", () => {
    modalOverlay.classList.add("show");
    taskInput.focus();
});

cancelTaskButton.addEventListener("click", () => {
    modalOverlay.classList.remove("show");
    taskInput.value = "";
});

addButton.addEventListener("click", () => {
    const taskName = taskInput.value.trim();

    if (taskName === "") {
        return;
    }

    const taskCard = document.createElement("div");
    taskCard.className = "task-card";
    taskCard.classList.add("task-card");
    taskCard.textContent = taskName;

    taskList.appendChild(taskCard);

    taskInput.value = "";
    modalOverlay.classList.remove("show");
    updateTaskCount();

    formData = new FormData();
    formData.append("taskboard_name", taskName);

    try {
        response = fetch ("http://localhost:8000/api/add_taskboard", {
        method: "POST",
        body: formData
    });
    } catch (error) {
        console.error("Error occured while adding taskboard to db:", error);
    }

});

taskInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        addButton.click();
    }
});

modalOverlay.addEventListener("click", (event) => {
    if (event.target === modalOverlay) {
        modalOverlay.classList.remove("show");
        taskInput.value = "";
    }
});

function updateTaskCount(){
    const taskCount = taskList.querySelectorAll(".task-card").length;
    if (taskCount === 0) {
        emptyText.classList.remove("hidden");
    }
    else {
        emptyText.classList.add("hidden");    
    };
};

async function renderTaskboard(taskboard_id) {
    try {
        const taskboard_response = await fetch(`http://localhost:8000/api/taskboard/${taskboard_id}`, {
            method: 'POST'
        });

        const navbar_response = await fetch('http://localhost:8000/api/navbar', {
            method: 'POST'
        });

        const taskboard_data = await taskboard_response.json();
        const navbar_data = await navbar_response.json();

        sessionStorage.setItem('preFetchedData', JSON.stringify({ ...taskboard_data, ...navbar_data}));

        window.location.href = 'taskboard.html';

    } catch (error) {
        console.error(`Error fetching taskboard data for ID ${taskboard_id}:`, error);
        return { taskboards: [] };
    }
}

async function load_taskboards() {
    const rawData = sessionStorage.getItem('preFetchedData');
    const data = rawData ? JSON.parse(rawData) : { taskboards: [] };

    for (const taskboard of data.taskboards) {
        const taskCard = document.createElement("button");
        taskCard.onclick = () => {
            renderTaskboard(taskboard.uuid);
        };
        taskCard.classList.add("task-card");
        taskCard.textContent = taskboard.taskboard_name;
        taskList.appendChild(taskCard);
    }

    updateTaskCount();
}

load_taskboards();