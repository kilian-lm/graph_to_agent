// <script>
function closeModal() {
    document.getElementById('user-message-modal').style.display = 'none';
}

// Automatically display the modal when the page loads
window.onload = function () {
    document.getElementById('user-message-modal').style.display = 'block';
}


document.addEventListener("DOMContentLoaded", function () {
    var mediaRecorder;
    var audioChunks = [];

    document.getElementById("start-recording").addEventListener("click", function () {
        document.getElementById("recording-status").innerHTML = "Recording...";
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
                    var audioBlob = new Blob(audioChunks, {type: "audio/wav"});

                    var formData = new FormData();
                    formData.append("audio", audioBlob);
                    var translationPrompt = document.getElementById("translation-prompt").value;
                    formData.append("translation-prompt", translationPrompt); // Add to FormData
                    var freshness = document.getElementById("freshness").value;


                    var frequencyPenalty = document.getElementById("frequency-penalty").value;


                    var maxTokens = document.getElementById("max_tokens").value;


                    formData.append("translation-prompt", translationPrompt);
                    formData.append("freshness", freshness);
                    formData.append("frequency-penalty", frequencyPenalty);
                    formData.append("max_tokens", maxTokens);

                    fetch("/upload-audio", {method: "POST", body: formData})
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById("recording-status").innerHTML = "";
                            document.getElementById("transcription").innerHTML = data.text;

                            // Update graph with data
                            updateGraph(data.graph_data);

                            function updateGraph(graph_data) {
                                // Example: Clear existing data and add new nodes/edges
                                nodes.clear();
                                edges.clear();
                                nodes.add(graph_data.nodes);
                                edges.add(graph_data.edges);
                            }
                        });
                };
                mediaRecorder.start();
            });
    });

    document.getElementById('freshness').addEventListener('change', function () {
        document.getElementById('freshness-value').innerText = this.value;
    });

    document.getElementById('max_tokens').addEventListener('change', function () {
        document.getElementById('max_tokens_value').innerText = this.value;
    });

    document.getElementById('frequency-penalty').addEventListener('change', function () {
        document.getElementById('frequency-penalty-value').innerText = this.value;
    });

    document.getElementById("stop-recording").addEventListener("click", function () {
        mediaRecorder.stop();
    });

    // Graph logic
    var nodes = new vis.DataSet([]);
    var edges = new vis.DataSet([]);

    // Provide data and options
    var data = {
        nodes: nodes,
        edges: edges
    };

    // Define options
    var options = {
        manipulation: {
            enabled: true, // Enable default manipulation controls
            initiallyActive: true,
            editNode: function (nodeData, callback) {
                // Show a text field pop-up to edit the node
                var newLabel = prompt("Enter new label:", nodeData.label);
                if (newLabel !== null) {
                    nodeData.label = newLabel;
                    callback(nodeData);
                } else {
                    callback(null); // Cancel the edit
                }
            }
            // Other customization options can be added here
        }
    };

    // Initialize the network
    var container = document.getElementById('graph');
    var network = new vis.Network(container, data, options);


});
// </script>
