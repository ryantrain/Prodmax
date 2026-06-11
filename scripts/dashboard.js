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

updateTaskCount();