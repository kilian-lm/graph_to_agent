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

    }

    init() {
        this.loadAvailableGraphs();
        this.setupNetwork();
        this.attachEventListeners();
    }

    // You'll also need to implement the resetJSON method
    resetJSON() {
        this.saveEntireGraphToJSON();
        console.log('JSON reset to current graph state.');
    }

    // Assuming you have a triggerAgents method implemented
    triggerAgents() {
        // Logic to trigger agents would go here
        console.log('Agents triggered.');
    }


    async loadAvailableGraphs() {
        try {
            const response = await fetch('/get-available-graphs');
            const graphs = await response.json();
            const dropdown = document.getElementById('graphDropdown');
            dropdown.innerHTML = '';
            graphs.forEach(graph => {
                const option = document.createElement('option');
                option.value = graph.graph_id;
                option.textContent = graph.graph_name;
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

    // updateGraph(graphData) {
    //     this.nodes.clear();
    //     this.edges.clear();
    //     this.nodes.add(graphData.nodes);
    //     this.edges.add(graphData.edges);
    //     this.saveEntireGraphToJSON();
    //     console.log('Graph updated:', graphData);
    // }

    // updateGraph(graphData) {
    //     this.nodes.clear();
    //     this.edges.clear();
    //
    //     // Update the nodes and edges separately to prevent duplicate items
    //     if (graphData.nodes && graphData.nodes.length > 0) {
    //         this.nodes.add(graphData.nodes);
    //     }
    //
    //     if (graphData.edges && graphData.edges.length > 0) {
    //         this.edges.add(graphData.edges);
    //     }
    //
    //     this.saveEntireGraphToJSON();
    //     console.log('Graph updated:', graphData);
    // }

    updateGraph(graphData) {
    this.nodes.clear();
    this.edges.clear();

    try {
        this.nodes.add(graphData.nodes);
        this.edges.add(graphData.edges);
    } catch (error) {
        if (error.toString().includes('item with id already exists')) {
            console.error('Duplicate node ID found, applying fix:', error);

            const fixedNodes = graphData.nodes.map(node => {
                // Append _fix to the ID of the node
                return {...node, id: `${node.id}_fix`};
            });

            try {
                this.nodes.add(fixedNodes);
                this.edges.add(graphData.edges);
            } catch (secondError) {
                console.error('Error after applying fix:', secondError);
            }
        } else {
            console.error('Error updating graph:', error);
        }
    }

    this.saveEntireGraphToJSON();
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
                hierarchicalRepulsion: {
                    centralGravity: 0.0,
                    springLength: 400,
                    springConstant: 0.01,
                    nodeDistance: 420,
                    damping: 0.02
                },
                solver: 'hierarchicalRepulsion'
            }
        };

        this.network = new vis.Network(container, data, options);
    }

    attachEventListeners() {
        // Event listener for graph selection dropdown
        document.getElementById('graphDropdown').addEventListener('change', (event) => {
            const selectedGraphId = event.target.value;
            console.log('Graph dropdown changed:', selectedGraphId);
            if (selectedGraphId) {
                this.loadGraphData(selectedGraphId);
            }
        });

        // Event listeners for other buttons and inputs
        document.getElementById('applyNodeChangesButton').addEventListener('click', this.applyNodeChanges.bind(this));
        document.getElementById('cancelNodeChangesButton').addEventListener('click', this.cancelNodeChanges.bind(this));
        document.getElementById('saveGraphButton').addEventListener('click', this.saveGraphData.bind(this));
        document.getElementById('centralGravity').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('springLength').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('springConstant').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('nodeDistance').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('damping').addEventListener('change', this.updatePhysics.bind(this));
        document.getElementById('updateFromJsonButton').addEventListener('click', this.updateGraphFromJSON.bind(this));
        document.getElementById('resetJsonButton').addEventListener('click', this.resetJSON.bind(this));
        document.getElementById('triggerAgentsButton').addEventListener('click', this.gptPostRequest.bind(this));
    }


    async gptPostRequest() {
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

            const data = await response.json();

            // if (data.status === 'success') {
            this.updateGraph(data.updatedGraph);
            //     } else {
            //         console.error('Failed to process GPT request:', data);
            //         alert('Failed to process GPT request.');
            //     }
            // } catch (error) {
            //     console.error('Error in GPT request:', error);
            //     alert('An error occurred while processing the GPT request.');
            // }
        } catch (error) {
            console.error('Error performing GPT request:', error);
            alert('An error occurred while processing the GPT request.');
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
        var centralGravity = parseFloat(document.getElementById("centralGravity").value);
        var springLength = parseInt(document.getElementById("springLength").value);
        var springConstant = parseFloat(document.getElementById("springConstant").value);
        var nodeDistance = parseInt(document.getElementById("nodeDistance").value);
        var damping = parseFloat(document.getElementById("damping").value);
        var newOptions = {
            physics: {
                hierarchicalRepulsion: {
                    centralGravity: centralGravity,
                    springLength: springLength,
                    springConstant: springConstant,
                    nodeDistance: nodeDistance,
                    damping: damping
                }
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