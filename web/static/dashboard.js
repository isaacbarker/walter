/*
Changes watering allowed states based on api
 */

wateringToggle           = document.getElementById("watering-toggle"); // toggle
let waterEnabled = true;

// Get watering initial state & set toggle
function getWaterState() {
    fetch("/water/allowed")
        .then(r => r.json())
        .then(data => {
            waterEnabled = data["enabled"];
            wateringToggle.checked = waterEnabled;
        })
}

// Watering toggle options

function disableWater() {
    fetch("/water/off", {
        method: "POST"
    }).then(res => {
        if (!res.ok) throw new Error("Request failed");
    })
    .catch(err => console.error(err));
}

function enableWater() {
    fetch("/water/on", {
        method: "POST"
    }).then(res => {
        if (!res.ok) throw new Error("Request failed");
    })
    .catch(err => console.error(err));
}

// Truth state polling
setInterval(getWaterState, 2000);

// Event listeners
wateringToggle.addEventListener("change", () => {
    if (wateringToggle.checked) {
        enableWater();
    } else {
        disableWater();
    }
});


