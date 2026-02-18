let mediaRecorder
let audioChunks = []
let stream
let countdownInterval
let timeLeft = 0

async function initMedia() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    document.getElementById("camera").srcObject = stream
}

document.addEventListener("DOMContentLoaded", async () => {
    await initMedia()
    document.getElementById("start-btn").onclick = startInterview
    document.getElementById("answer-btn").onclick = startRecording
    document.getElementById("stop-btn").onclick = stopRecording
})

async function startInterview() {
    await fetch(`/interview/start/${candidateId}/${role}`, { method: "POST" })
    document.getElementById("start-btn").disabled = true
    await loadNextQuestion()
}

async function loadNextQuestion() {
    const res = await fetch(`/interview/question/${candidateId}`)
    const data = await res.json()

    if (data.status === "finished") {
        document.getElementById("question").innerText =
            "Thank you for your time. You may close this window."
        document.getElementById("timer").innerText = ""
        document.getElementById("answer-btn").disabled = true
        document.getElementById("stop-btn").disabled = true
        return
    }

    document.getElementById("question").innerText = data.question
    startTimer(data.time_limit)
    document.getElementById("answer-btn").disabled = false
}

function startTimer(seconds) {
    clearInterval(countdownInterval)
    timeLeft = seconds

    document.getElementById("timer").innerText = `Time left: ${timeLeft}s`

    countdownInterval = setInterval(() => {
        timeLeft--
        document.getElementById("timer").innerText = `Time left: ${timeLeft}s`

        if (timeLeft <= 0) {
            clearInterval(countdownInterval)
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop()
            } else {
                loadNextQuestion()
            }
        }
    }, 1000)
}

function startRecording() {
    document.getElementById("answer-btn").disabled = true
    document.getElementById("stop-btn").disabled = false

    audioChunks = []
    mediaRecorder = new MediaRecorder(stream)

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data)

    mediaRecorder.onstop = async () => {
        document.getElementById("stop-btn").disabled = true

        const blob = new Blob(audioChunks, { type: "audio/webm" })
        const formData = new FormData()
        formData.append("audio", blob)

        await fetch(`/interview/answer/${candidateId}`, {
            method: "POST",
            body: formData
        })

        loadNextQuestion()
    }

    mediaRecorder.start()
}

function stopRecording() {
    if (mediaRecorder) mediaRecorder.stop()
}
