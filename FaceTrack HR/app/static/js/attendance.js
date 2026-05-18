(() => {
    const config = window.attendanceConfig || {};
    const recognizeUrl = config.recognizeUrl;
    const pollingIntervalMs = Number(config.pollingIntervalMs || 2200);

    const videoEl = document.getElementById("cameraFeed");
    const canvasEl = document.getElementById("captureCanvas");
    const statusEl = document.getElementById("recognitionStatus");
    const logEl = document.getElementById("eventsLog");
    const startBtn = document.getElementById("startCameraBtn");
    const stopBtn = document.getElementById("stopCameraBtn");

    const cardEl = document.getElementById("recognizedEmployeeCard");
    const photoEl = document.getElementById("recognizedPhoto");
    const nameEl = document.getElementById("recognizedName");
    const metaEl = document.getElementById("recognizedMeta");
    const confidenceEl = document.getElementById("recognizedConfidence");

    let mediaStream = null;
    let timerId = null;
    let requestInFlight = false;

    if (!videoEl || !canvasEl || !statusEl || !startBtn || !stopBtn) {
        return;
    }

    function setStatus(message, level = "neutral") {
        statusEl.textContent = message;
        statusEl.className = "status-box";
        statusEl.classList.add(`status-${level}`);
    }

    function appendEvent(message, level = "neutral") {
        const line = document.createElement("div");
        line.className = "event-item";
        const now = new Date().toLocaleTimeString();
        line.innerHTML = `<strong>[${now}]</strong> ${message}`;
        if (level === "danger") {
            line.style.color = "#991b1b";
        }
        if (logEl.firstElementChild && logEl.firstElementChild.classList.contains("text-muted")) {
            logEl.innerHTML = "";
        }
        logEl.prepend(line);
    }

    function updateEmployeeCard(payload) {
        if (!payload || !payload.employee) {
            cardEl.classList.add("d-none");
            return;
        }
        const employee = payload.employee;
        cardEl.classList.remove("d-none");
        photoEl.src = employee.photo_url || "";
        nameEl.textContent = employee.full_name || "-";
        metaEl.textContent = `${employee.department || "Без отдела"} | ${employee.position || "-"}`;
        confidenceEl.textContent = `Уверенность: ${payload.confidence ?? "-"}%`;
    }

    function stopLoop() {
        if (timerId) {
            clearInterval(timerId);
            timerId = null;
        }
    }

    function stopCamera() {
        stopLoop();
        if (mediaStream) {
            mediaStream.getTracks().forEach((track) => track.stop());
            mediaStream = null;
        }
        videoEl.srcObject = null;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        setStatus("Камера остановлена.", "neutral");
    }

    async function sendFrame() {
        if (!mediaStream || requestInFlight) {
            return;
        }
        if (videoEl.videoWidth === 0 || videoEl.videoHeight === 0) {
            return;
        }

        requestInFlight = true;
        try {
            canvasEl.width = videoEl.videoWidth;
            canvasEl.height = videoEl.videoHeight;
            const ctx = canvasEl.getContext("2d");
            ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

            const image = canvasEl.toDataURL("image/jpeg", 0.85);
            const response = await fetch(recognizeUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image })
            });

            const payload = await response.json();
            if (payload.status === "recognized") {
                setStatus(payload.message || "Сотрудник распознан.", "success");
                appendEvent(payload.message || "Успешное распознавание.", "success");
                updateEmployeeCard(payload);
            } else if (payload.status === "unknown") {
                setStatus(payload.message || "Лицо не распознано.", "warning");
                appendEvent(payload.message || "Неизвестное лицо.", "neutral");
                updateEmployeeCard(null);
            } else if (payload.status === "no_face") {
                setStatus(payload.message || "Лицо не обнаружено.", "warning");
                updateEmployeeCard(null);
            } else {
                setStatus(payload.message || "Ошибка распознавания.", "danger");
                appendEvent(payload.message || "Ошибка распознавания.", "danger");
            }
        } catch (err) {
            setStatus(`Ошибка запроса: ${err.message}`, "danger");
            appendEvent(`Ошибка запроса: ${err.message}`, "danger");
        } finally {
            requestInFlight = false;
        }
    }

    async function startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("Браузер не поддерживает работу с веб-камерой.", "danger");
            appendEvent("Браузер не поддерживает getUserMedia.", "danger");
            return;
        }

        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            videoEl.srcObject = mediaStream;
            await videoEl.play();

            startBtn.disabled = true;
            stopBtn.disabled = false;

            setStatus("Камера запущена. Идет сканирование...", "success");
            appendEvent("Камера успешно запущена.");

            stopLoop();
            timerId = setInterval(sendFrame, pollingIntervalMs);
        } catch (err) {
            setStatus("Веб-камера не найдена или доступ запрещен.", "danger");
            appendEvent(`Ошибка камеры: ${err.message}`, "danger");
        }
    }

    startBtn.addEventListener("click", startCamera);
    stopBtn.addEventListener("click", stopCamera);
    window.addEventListener("beforeunload", stopCamera);
})();
