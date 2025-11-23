// TODO: Connect to FastAPI 
const API_BASE = "http://localhost:8000/api";  // Change if needed

async function loadUsers() {
    try {
        const res = await fetch(`${API_BASE}/users/`);
        const data = await res.json();

        const userList = document.getElementById("userList");
        userList.innerHTML = "";

        data.forEach(user => {
            const li = document.createElement("li");
            li.className = "list-group-item";
            li.textContent = `${user.id}: ${user.name}`;
            userList.appendChild(li);
        });
    } catch (err) {
        alert("API request failed. Check backend is running.");
        console.error(err);
    }
}
