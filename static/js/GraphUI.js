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

        // Define selectionRectangle as a class property
        this.selectionRectangle = document.createElement('div');
        this.selectionRectangle.style.position = 'absolute';
        this.selectionRectangle.style.border = '1px dashed #999';
        this.selectionRectangle.style.background = 'rgba(200, 200, 200, 0.3)';
        this.selectionRectangle.style.pointerEvents = 'none';
        document.body.appendChild(this.selectionRectangle);

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


    // updateGraph(graphData) {
    //     this.nodes.clear();
    //     this.edges.clear();
    //     this.nodes.add(graphData.nodes);
    //     this.edges.add(graphData.edges);
    //     this.saveEntireGraphToJSON();
    //     console.log('Graph updated:', graphData);
    // }


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


    moveSelectedNodes(selectedNodes) {
        // Implement the code to move the selected nodes as a group
        // Example:
        const offsetX = 50; // Adjust this based on your requirements
        const offsetY = 50; // Adjust this based on your requirements

        // Get the current positions of the selected nodes
        const currentPositions = this.nodes.get(selectedNodes, {fields: ['x', 'y']});

        // Calculate the new positions
        const newPositions = currentPositions.map(({x, y}) => ({
            x: x + offsetX,
            y: y + offsetY
        }));

        // Update the positions of the selected nodes
        this.nodes.update(newPositions);
    }


    updateSelection(selectedNodes) {
        // Implement the code to visually indicate the selected nodes (e.g., change their appearance)
        // You can add a border or change the color of the selected nodes.
        // Example:
        this.nodes.update(selectedNodes.map(node => ({id: node, borderWidth: 2})));
    }

    // clearSelectionArea() {
    //     // Implement the code to clear the selection area (e.g., remove the highlighting rectangle)
    //     // You can hide or remove the selection rectangle.
    // }


    highlightSelectionArea(rect) {
        // Use this.selectionRectangle instead of selectionRectangle
        this.selectionRectangle.style.left = rect.x + 'px';
        this.selectionRectangle.style.top = rect.y + 'px';
        this.selectionRectangle.style.width = rect.width + 'px';
        this.selectionRectangle.style.height = rect.height + 'px';
    }

    selectElementsWithCursor() {
        let startX, startY, isSelecting = false;
        let selectedNodes = [];

        this.network.on('dragStart', (event) => {
            if (!event.nodes.length) {
                startX = event.pointer.canvas.x;
                startY = event.pointer.canvas.y;
                isSelecting = true;
                selectedNodes = [];
            }
        });

        this.network.on('dragging', (event) => {
            if (isSelecting) {
                const currentX = event.pointer.canvas.x;
                const currentY = event.pointer.canvas.y;
                const rect = {
                    x: Math.min(startX, currentX),
                    y: Math.min(startY, currentY),
                    width: Math.abs(currentX - startX),
                    height: Math.abs(currentY - startY)
                };

                // Highlight the selection area (you can add your own styling)
                this.highlightSelectionArea(rect);

                // Convert rectangle from canvas to DOM coordinates
                const DOMRect = this.network.canvasToDOM({
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                });

                // Now we need to determine which nodes fall within this rectangle
                selectedNodes = this.nodes.getIds().filter((id) => {
                    const nodePosition = this.network.getPositions(id)[id];
                    const nodeDOMPosition = this.network.canvasToDOM(nodePosition);
                    return (
                        nodeDOMPosition.x >= DOMRect.x &&
                        nodeDOMPosition.x <= DOMRect.x + DOMRect.width &&
                        nodeDOMPosition.y >= DOMRect.y &&
                        nodeDOMPosition.y <= DOMRect.y + DOMRect.height
                    );
                });

                // Update the visual selection (you can add your own styling)
                this.updateSelection(selectedNodes);
            }
        });

        this.network.on('dragEnd', () => {
            if (isSelecting) {
                isSelecting = false;

                // Move the selected nodes as a group
                this.moveSelectedNodes(selectedNodes);

                // Clear the selection area and update the visual selection
                this.clearSelectionArea();
                this.updateSelection(selectedNodes);
            }
        });
    }

}

// Usage
const graphUI = new GraphUI();
graphUI.init();