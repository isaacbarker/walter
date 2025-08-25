// init chart
const canvas = document.getElementById("soilMoisture");
const ctx = canvas.getContext("2d");

// scale canvas to screen width
if (window.innerWidth < 1080) {
    canvas.width = 0.75 * window.innerWidth;
} else {
    canvas.width = 800; 
}

let chart = new Chart(ctx, {
    type: "line",
    data: {    
        labels: [],
        datasets: [{
            data: [],
            fill: true,
            borderColor: '#8ec07c',
            tension: 0.1
        }]
    },
    options: {
        responsive: false,
        maintainAspectRatio: true,
        scales: {
            x: {
                type: "time",
                time: {
                    tooltipFormat: "dd/MM/yyyy HH:mm", // hover format
                    displayFormats: {
                        minute: "HH:mm",
                        hour: "dd/MM HH:mm",
                        day: "dd/MM/yyyy",
                        month: "MMM yyyy"
                    }
                },
                grid: {
                    display: false
                },
                border: {
                    color: '#fbf1c7'
                },
                ticks: {
                    source: "auto",
                    color: '#fbf1c7'
                }
            },
            y: {
                title: {
                    text: "Soil Moisture / %",
                    display: true,
                    color: '#fbf1c7'
                },
                ticks: {
                    color: '#fbf1c7'
                },
                grid: {
                    display: false
                },
                border: {
                    color: '#fbf1c7'
                },
            }
        },
        plugins: {
            legend:  {
                display: false
            },
            decimation: {
                enabled: true,
                algorithm: 'min-max', // preserves peaks and valleys
                samples: 100 // keep ~200 points max
            }
        }
    },
});

// load in stats and change based on data
const soilMoisture = document.getElementById("soil");
const lastWatered = document.getElementById("water");
const countdown = document.getElementById("countdown")

// poll every 10s for new data
const interval = 1 * 60 * 1000
let dataRange = 12 * 60 * 60;
let nextPollTime = Date.now();

let intervalCountdownId;
let intervalLoopId;

// get dataRange
const dataRangeSelect = document.getElementById("data-range");

dataRangeSelect.addEventListener('change', () => {
    dataRange = dataRangeSelect.value * 60 * 60;
    // reset
    clearInterval(intervalLoopId);
    getData();
    intervalId = setInterval(getData, interval)
})

// grab data from source and prep for chart
const getData = () => {
    nextPollTime = Date.now() + interval;

    // clear any existing countdown first
    if (intervalCountdownId) clearInterval(intervalCountdownId);

    // start countdown display
    intervalCountdownId = setInterval(() => {
        const now = Date.now();
        let timeLeftMs = nextPollTime - now;

        if (timeLeftMs <= 0) {
            countdown.innerHTML = "Time to next refresh: 00:00";
            return;
        }

        const timeLeftS = Math.floor(timeLeftMs / 1000);
        const minutes = Math.floor(timeLeftS / 60).toString().padStart(2, '0');
        const seconds = (timeLeftS % 60).toString().padStart(2, '0');
        countdown.innerHTML = `Time to next refresh: ${minutes}:${seconds}`;
    }, 1000);

    // get data since the range
    fetch(`/reading?since=${dataRange}`)
        .then(response => response.json())
        .then(readings => {
            let labels = [];
            let data = [];

            for (let i = 0; i < readings.length; i++) {
                const reading = readings[i];
                data.push(reading["soil_moisture"]);
                const time_ms = reading["time"] * 1000;
                labels.push(time_ms)
            }

            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            console.info("Refreshed readings from server: updating graph with results.")
            chart.update()

            const last_reading = readings[readings.length - 1]
            soilMoisture.innerHTML = `${last_reading["soil_moisture"]}%`
            
        })
        .catch(err => console.error(`Error occured when polling data: ${err}`));

    // get last watered
    fetch("/water")
        .then(response => response.json())
        .then(data => {
            const lastWateredMs = data["last_watered"] * 1000
            const date = new Date(lastWateredMs)
            const day = date.getDate();
            const month = String(date.getMonth()).padStart(2, '0');
            const year = String(date.getFullYear()).slice(2,4)
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            lastWatered.innerHTML = `${day}/${month}/${year} ${hours}:${minutes}`
            console.info("Refreshed last watered from server")
        })
        .catch(err => console.error(`Error occured when polling data: ${err}`));
};

getData();

intervalLoopId = setInterval(getData, interval)