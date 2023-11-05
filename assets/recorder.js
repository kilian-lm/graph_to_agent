document.addEventListener("DOMContentLoaded", function () {
    var mediaRecorder;
    var audioChunks = [];

    document.getElementById("start-recording").addEventListener("click", function () {
        // Show recording status (you can customize this part as needed)
        var recordingStatus = document.getElementById("recording-status");
        recordingStatus.innerHTML = "Recording...";
        recordingStatus.classList.add("recording");

        navigator.mediaDevices.getUserMedia({audio: true})
            .then(function (stream) {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.onstart = function () {
                    audioChunks = [];
                };
                mediaRecorder.ondataavailable = function (event) {
                    audioChunks.push(event.data);
                };
                mediaRecorder.onstop = function () {
                    var audioBlob = new Blob(audioChunks, {type: "audio/mp3"});
                    var formData = new FormData();
                    formData.append("audio", audioBlob);
                    fetch("/upload-audio", {method: "POST", body: formData});
                };
                mediaRecorder.start();
            });
    });

    document.getElementById("stop-recording").addEventListener("click", function () {
        // Hide recording status
        var recordingStatus = document.getElementById("recording-status");
        recordingStatus.innerHTML = "";
        recordingStatus.classList.remove("recording");

        mediaRecorder.stop();
    });
});
