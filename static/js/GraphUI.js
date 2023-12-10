class GraphUI {
    constructor() {
        this.nodes = new vis.DataSet();
        this.edges = new vis.DataSet();
        this.currentNodeId = null;
        this.network = null;

        // Bind class methods
        this.loadAvailableGraphs = this.loadAvailableGraphs.bind(this);
        this.loadGraphData = this.loadGraphData.bind(this);
        this.updateGraph = this.updateGraph.bind(this);
        this.saveEntireGraphToJSON = this.saveEntireGraphToJSON.bind(this);
        this.setupNetwork = this.setupNetwork.bind(this);
        this.attachEventListeners = this.attachEventListeners.bind(this);
        this.handleSelection = this.handleSelection.bind(this);
        this.editNodeFunction = this.editNodeFunction.bind(this);
        this.applyNodeChanges = this.applyNodeChanges.bind(this);
        this.cancelNodeChanges = this.cancelNodeChanges.bind(this);
        this.saveGraphData = this.saveGraphData.bind(this);
        this.updatePhysics = this.updatePhysics.bind(this);
        this.updateGraphFromJSON = this.updateGraphFromJSON.bind(this);
        this.gptPostRequest = this.gptPostRequest.bind(this);

        // physics

        this.defaultPhysics = {
            centralGravity: 0.01,
            springLength: 50,
            springConstant: 0.01,
            nodeDistance: 50,
            damping: 0.1,
            solver: 'hierarchicalRepulsion',
            // avoidOverlap: true // To prevent node overlap

        };

        // msg passing
        this.createMessagePassingDropdown = this.createMessagePassingDropdown.bind(this);
        this.handleMessagePassingChange = this.handleMessagePassingChange.bind(this);

        // add copy-paste
        this.copiedData = null;

    }

    startCountdown(duration) {
        let timer = duration, minutes, seconds, milliseconds;
        const countdownElement = document.getElementById('countdownTimer');
        const interval = setInterval(function () {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);
            milliseconds = parseInt((timer - Math.floor(timer)) * 100, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;
            milliseconds = milliseconds < 10 ? "0" + milliseconds : milliseconds;

            countdownElement.textContent = minutes + ":" + seconds + ":" + milliseconds;

            if ((timer -= 0.01) <= 0) {
                clearInterval(interval);
                countdownElement.textContent = 'Sending Graph-Data back to UI, get ready to get blown!';
            }
        }, 10); // Update every 10ms for smooth countdown
    }


    // add copy
    copySelection() {
        const selectedNodes = this.nodes.get(this.network.getSelectedNodes());
        const selectedEdges = this.edges.get(this.network.getSelectedEdges());

        const timestamp = new Date().getTime();
        this.copiedData = {
            nodes: selectedNodes.map(node => ({...node, id: `copied-${timestamp}-${node.id}`})),
            edges: selectedEdges.map(edge => ({
                ...edge,
                id: `copied-${timestamp}-${edge.id}`,
                from: selectedNodes.some(n => n.id === edge.from) ? `copied-${timestamp}-${edge.from}` : edge.from,
                to: selectedNodes.some(n => n.id === edge.to) ? `copied-${timestamp}-${edge.to}` : edge.to,
            }))
        };
    }

    // paste functionality
    pasteSelection() {
        if (!this.copiedData) {
            alert('No nodes copied!');
            return;
        }

        this.nodes.add(this.copiedData.nodes);
        this.edges.add(this.copiedData.edges);

        // Clear the copiedData after pasting
        this.copiedData = null;
    }

    // msg passing

    // Method to create and populate the message-passing dropdown
    createMessagePassingDropdown() {
        const techniques = [
            {value: 'flooding', text: 'Flooding/Broadcasting'},
            {value: 'random_walk', text: 'Random Walk'},
            {value: 'gossip', text: 'Gossip Protocol'},
            {value: 'shortest_path', text: 'Shortest Path Routing'},
            {value: 'distance_vector', text: 'Distance Vector Routing'},
            {value: 'link_state', text: 'Link State Routing'},
            {value: 'hierarchical', text: 'Hierarchical Routing'},
            {value: 'recursive', text: 'Recursive Message Passing'},
            {value: 'layered', text: 'Layered Message Passing'},
            {value: 'token_passing', text: 'Token Passing'}
        ];

        const dropdown = document.getElementById('messagePassingDropdown');
        dropdown.innerHTML = '';

        techniques.forEach(technique => {
            const option = document.createElement('option');
            option.value = technique.value;
            option.text = technique.text;
            dropdown.appendChild(option);
        });

        dropdown.addEventListener('change', this.handleMessagePassingChange);
    }

    handleMessagePassingChange(event) {
        const selectedTechnique = event.target.value;
        console.log('Selected message-passing technique:', selectedTechnique);
    }


    init() {
        this.loadAvailableGraphs();
        this.setupNetwork();
        this.attachEventListeners();
        this.createMessagePassingDropdown();
        this.loadOpenAIModels();


    }

    // You'll also need to implement the resetJSON method
    resetJSON() {
        this.saveEntireGraphToJSON();
        console.log('JSON reset to current graph state.');
    }


    // async loadAvailableGraphs() {
    //     try {
    //         const response = await fetch('/get-available-graphs');
    //         const graphs = await response.json();
    //         const dropdown = document.getElementById('graphDropdown');
    //         dropdown.innerHTML = '';
    //         graphs.forEach(graph => {
    //             const option = document.createElement('option');
    //             option.value = graph.graph_id;
    //             option.textContent = graph.graph_name;
    //             dropdown.appendChild(option);
    //         });
    //         console.log('Available graphs loaded:', graphs);
    //     } catch (error) {
    //         console.error('Error loading available graphs:', error);
    //     }
    // }

    async loadAvailableGraphs() {
        try {
            const response = await fetch('/get-available-graphs');
            const graphs = await response.json();
            const dropdown = document.getElementById('graphDropdown');
            dropdown.innerHTML = '';
            graphs.forEach(graph => {
                const option = document.createElement('option');
                option.value = graph.graph_id;  // Use graph_id as the value
                option.textContent = graph.graph_name;  // Display the user-friendly string
                dropdown.appendChild(option);
            });
            console.log('Available graphs loaded:', graphs);
        } catch (error) {
            console.error('Error loading available graphs:', error);
        }
    }

    async loadGraphData(graphId) {
        try {
            const response = await fetch('/get-graph-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    graph_id: graphId
                })
            });
            const graphData = await response.json();
            this.updateGraph(graphData);
            console.log('Graph data loaded:', graphData);
        } catch (error) {
            console.error('Error loading graph data:', error);
        }
    }


    updateGraph(graphData) {
        // Clear the existing data
        this.nodes.clear();
        this.edges.clear();

        // Add new nodes, checking for duplicates
        graphData.nodes.forEach(node => {
            if (!this.nodes.get(node.id)) {
                this.nodes.add(node);
            } else {
                console.warn(`Node with id ${node.id} already exists. Skipping...`);
                // Optionally, update the existing node here
                // this.nodes.update(node);
            }
        });

        // Add edges
        this.edges.add(graphData.edges);

        // Additional logic if needed
        console.log('Graph updated:', graphData);
    }


    saveEntireGraphToJSON() {
        var graphData = {
            nodes: this.nodes.get(),
            edges: this.edges.get()
        };
        document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
    }

    setupNetwork() {
        var container = document.getElementById('graph');
        var data = {
            nodes: this.nodes,
            edges: this.edges
        };
        var options = {
            manipulation: {
                enabled: true,
                initiallyActive: true,
                multiselect: true,
                editNode: this.editNodeFunction,
                addNode: this.addNodeFunction,
                deleteNode: this.deleteNodeFunction
            },
            physics: {
                enabled: true,
                [this.defaultPhysics.solver]: {
                    centralGravity: this.defaultPhysics.centralGravity,
                    springLength: this.defaultPhysics.springLength,
                    springConstant: this.defaultPhysics.springConstant,
                    nodeDistance: this.defaultPhysics.nodeDistance,
                    damping: this.defaultPhysics.damping
                },
                solver: this.defaultPhysics.solver
            }
        };

        this.network = new vis.Network(container, data, options);
    }

    attachEventListeners() {

        // Set the initial values for the HTML elements from the default physics settings
        document.getElementById('centralGravity').value = this.defaultPhysics.centralGravity;
        document.getElementById('springLength').value = this.defaultPhysics.springLength;
        document.getElementById('springConstant').value = this.defaultPhysics.springConstant;
        document.getElementById('nodeDistance').value = this.defaultPhysics.nodeDistance;
        document.getElementById('damping').value = this.defaultPhysics.damping;
        document.getElementById('physicsSolver').value = this.defaultPhysics.solver;

        // Update physics settings when control values are changed by the user
        document.getElementById('centralGravity').addEventListener('change', () => this.updatePhysics());
        document.getElementById('springLength').addEventListener('change', () => this.updatePhysics());
        document.getElementById('springConstant').addEventListener('change', () => this.updatePhysics());
        document.getElementById('nodeDistance').addEventListener('change', () => this.updatePhysics());
        document.getElementById('damping').addEventListener('change', () => this.updatePhysics());
        document.getElementById('physicsSolver').addEventListener('change', () => this.updatePhysics());

        // Event listener for graph selection dropdown
        document.getElementById('graphDropdown').addEventListener('change', (event) => {
            const selectedGraphId = event.target.value;
            console.log('Graph dropdown changed:', selectedGraphId);
            if (selectedGraphId) {
                this.loadGraphData(selectedGraphId);
            }
        });

        // ToDo :: Message passing dropdown  (still to do, but very complex, consider RL)

        const messagePassingDropdown = document.getElementById('messagePassingDropdown');
        if (messagePassingDropdown) {
            messagePassingDropdown.addEventListener('change', this.handleMessagePassingChange);
        } else {
            console.error('Message passing dropdown not found');
        }

        // Add event listeners for copy and paste actions
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.key === 'c') { // Ctrl+C for copy
                event.preventDefault(); // Prevent the default copy action
                this.copySelection();
            } else if (event.ctrlKey && event.key === 'v') { // Ctrl+V for paste
                event.preventDefault(); // Prevent the default paste action
                this.pasteSelection();
            }
        });


        // Event listeners for other buttons and inputs
        document.getElementById('applyNodeChangesButton').addEventListener('click', this.applyNodeChanges.bind(this));
        document.getElementById('cancelNodeChangesButton').addEventListener('click', this.cancelNodeChanges.bind(this));
        // document.getElementById('saveGraphButton').addEventListener('click', this.saveGraphData.bind(this));
        document.getElementById('centralGravity').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('springLength').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('springConstant').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('nodeDistance').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('damping').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('updateFromJsonButton').addEventListener('click', this.updateGraphFromJSON.bind(this));
        document.getElementById('resetJsonButton').addEventListener('click', this.resetJSON.bind(this));
        document.getElementById('triggerAgentsButton').addEventListener('click', this.gptPostRequest.bind(this));
    }


    async loadOpenAIModels() {
        try {
            const response = await fetch('/get-openai-models');
            const models = await response.json();
            const dropdown = document.getElementById('openaiModelDropdown');
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.value;
                option.textContent = model.label;
                dropdown.appendChild(option);
            });
            console.log('OpenAI models loaded:', models);
        } catch (error) {
            console.error('Error loading OpenAI models:', error);
        }
    }

    async gptPostRequest() {
        // Show the loading indicator
        this.startCountdown(130); // Start a 130-second countdown

        document.getElementById('loadingIndicator').style.display = 'block';

        try {
            var graphData = {
                nodes: this.nodes.get(),
                edges: this.edges.get()
            };

            console.log('Graph data being sent to backend:', graphData);

            const response = await fetch('/return-gpt-agent-answer-to-graph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(graphData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            console.log('Full response data received:', data);

            if (data && data.updated_graph && Array.isArray(data.updated_graph.nodes) && Array.isArray(data.updated_graph.edges)) {
                this.updateGraph(data.updated_graph); // Update with the updated_graph data
                // Alert the user about the saved name of the graph
                alert('Your graph has been saved under the name: ' + data.saved_name);
            } else {
                console.error('Invalid or incomplete data received from backend:', data);
                alert('Invalid or incomplete data received from backend.');
            }
        } catch (error) {
            console.error('Error in GPT request:', error);
            alert(`An error occurred while processing the GPT request: ${error.message}`);
        } finally {
            // Hide the loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
        }
    }


    handleSelection(params) {
        console.log('Selected nodes:');
        console.log(params.nodes);

        console.log('Selected edges:');
        console.log(params.edges);

        // Perform actions on the selected nodes and edges
    }

    editNodeFunction(nodeData, callback) {
        this.currentNodeId = nodeData.id;
        document.getElementById('nodeTextLabel').value = nodeData.label;
        document.getElementById('editPanel').style.display = 'block';
        console.log('Editing node:', this.currentNodeId);
    }

    applyNodeChanges() {
        var newLabel = document.getElementById('nodeTextLabel').value;
        this.nodes.update({id: this.currentNodeId, label: newLabel});
        document.getElementById('editPanel').style.display = 'none';
        this.saveEntireGraphToJSON();
        this.network.setOptions({manipulation: {initiallyActive: true}});
        console.log('Node changes applied:', this.currentNodeId, newLabel);
    }

    cancelNodeChanges() {
        document.getElementById('editPanel').style.display = 'none';
        this.saveEntireGraphToJSON();
        this.network.setOptions({manipulation: {initiallyActive: true}});
        console.log('Node changes canceled:', this.currentNodeId);
    }

    saveGraphData() {
        var graphData = {
            nodes: this.nodes.get(),
            edges: this.edges.get()
        };
        document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
        console.log('Saving graph data:', graphData);
        fetch('/save-graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(graphData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Graph saved successfully!');
                } else {
                    alert('Graph saved successfully, just need to adapt servser side success msg!');
                }
            })
            .catch(error => {
                console.error('Error saving graph:', error);
                alert('An error occurred while saving the graph.');
            });
    }

    updatePhysics() {
        // Get the values from the HTML elements
        var centralGravity = parseFloat(document.getElementById("centralGravity").value);
        var springLength = parseInt(document.getElementById("springLength").value);
        var springConstant = parseFloat(document.getElementById("springConstant").value);
        var nodeDistance = parseInt(document.getElementById("nodeDistance").value);
        var damping = parseFloat(document.getElementById("damping").value);
        var solver = document.getElementById("physicsSolver").value;

        // Apply the new physics settings to the network
        var newOptions = {
            physics: {
                enabled: true,
                [solver]: {
                    centralGravity: centralGravity,
                    springLength: springLength,
                    springConstant: springConstant,
                    nodeDistance: nodeDistance,
                    damping: damping,
                    // avoidOverlap: true // To prevent node overlap

                },
                solver: solver
            }
        };
        this.network.setOptions(newOptions);
        console.log('Physics updated:', newOptions);
    }


    updateGraphFromJSON() {
        var jsonData = document.getElementById('jsonData').value;
        try {
            var graphData = JSON.parse(jsonData);
            this.nodes.clear();
            this.edges.clear();
            this.nodes.add(graphData.nodes);
            this.edges.add(graphData.edges);
            console.log('Graph updated from JSON:', graphData);
        } catch (error) {
            alert('Invalid JSON format.');
            console.error('Invalid JSON format:', error);
        }
    }
}

// Usage
const graphUI = new GraphUI();
graphUI.init();