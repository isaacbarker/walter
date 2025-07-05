// init chart
const canvas = document.getElementById("chart");
const ctx = canvas.getContext("2d");

// scale canvas to screen width
if (window.innerWidth < 1920) {
    canvas.width = 0.75 * window.innerWidth;
} else {
    canvas.width = 900; 
}

// configure linear gradient for line area fill
const fillGradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
fillGradient.addColorStop(0, "#296da999");
fillGradient.addColorStop(1, "#9CC1D922");

let chart = new Chart(ctx, {
    type: "line",
    data: {    
        labels: [],
        datasets: [{
            data: [],
            fill: true,
            borderColor: '#296da999',
            backgroundColor: fillGradient,
            tension: 0.1
        }]
    },
    options: {
        responsive: false,
        maintainAspectRatio: true,
        animations: {
            tension: {
                duration: 1000,
                easing: 'linear',
                from: 0,
                to: 0.5,
                loop: true
            }
        },
        scales: {
            x: {
                type: "time",
                time: {
                    unit: "minute",
                    stepSize: 30,
                    displayFormats: {
                        minute: "HH:mm",
                    },
                },
                grid: {
                    display: false
                },
                border: {
                    color: '#57697d'
                },
                ticks: {
                    source: "auto",
                    color: '#57697d'
                },
            },
            y: {
                title: {
                    text: "Soil Moisture / %",
                    display: true,
                    color: '#57697d'
                },
                ticks: {
                    color: '#57697d'
                },
                min: 0,
                max: 100,
                grid: {
                    display: false
                },
                border: {
                    color: '#57697d'
                },
            }
        },
        plugins: {
            legend:  {
                display: false
            }
        }
    },
});

// load in stats and change based on data
const soilMoisture = document.getElementById("soil");
const lastWatered = document.getElementById("water");
const countdown = document.getElementById("countdown")

// poll every 5 mins for new data
const interval = 1/6 * 60 * 1000

// grab data from source and prep for chart
const getData = () => {

    // start countdown until next poll
    let timeLeftMs = interval

    const intervalId = setInterval(() => {
        timeLeftS = timeLeftMs / 1000;
        minutes = Math.floor(timeLeftS / 60).toString().padStart(2, '0');
        seconds = (timeLeftS % 60).toString().padStart(2, '0');
        
        if (timeLeftS <= 0) {
            countdown.innerHTML = "Time to next refresh: 00:00";
            clearInterval(intervalId); // stop the countdown
            return;
        }
        
        countdown.innerHTML = `Time to next refresh: ${minutes}:${seconds}`
        timeLeftMs -= 1000;
    }, 1000)

    // get last 3 hrs of readings
    fetch(`/reading?since=${1 * 60 * 60}`)
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

            const last_reading = readings[readings.length - 1]
            soilMoisture.innerHTML = `Soil Moisture: ${last_reading["soil_moisture"]}%`

            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            console.info("Refreshed readings from server: updating graph with results.")
            chart.update()
            
        })
        .catch(err => console.error(`Error occured when polling data: ${err}`));

    // get last watered
    fetch("/water")
        .then(response => response.json())
        .then(data => {
            const lastWateredMs = data["last_watered"] * 1000
            const date = new Date(lastWateredMs)
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            lastWatered.innerHTML = `Last Watered: ${hours}:${minutes}`
            console.info("Refreshed last watered from server")
        })
        .catch(err => console.error(`Error occured when polling data: ${err}`));
};

getData();

setInterval(getData, interval)