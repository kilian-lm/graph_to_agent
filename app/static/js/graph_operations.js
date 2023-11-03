document.getElementById('graphDropdown').addEventListener('change', async function () {
    const selectedGraphId = this.value;
    if (selectedGraphId) {
        try {
            const response = await fetch('/get-graph-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({graph_id: selectedGraphId})
            });
            const graphData = await response.json();
            network.setData(graphData);
        } catch (error) {
            console.error('Error loading graph data:', error);
        }
    }
});

async function loadAvailableGraphs() {
    try {
        const response = await fetch('/get-available-graphs');
        const graphs = await response.json();
        const dropdown = document.getElementById('graphDropdown');
        graphs.forEach(graph => {
            const option = document.createElement('option');
            option.value = graph.graph_id;
            option.textContent = graph.graph_name;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading available graphs:', error);
    }
}

loadAvailableGraphs();

var nodes = new vis.DataSet();
var edges = new vis.DataSet();
var currentNodeId;

function editNodeFunction(nodeData, callback) {
    currentNodeId = nodeData.id;
    document.getElementById('nodeTextLabel').value = nodeData.label;
    document.getElementById('editPanel').style.display = 'block';
}

function applyNodeChanges() {
    var newLabel = document.getElementById('nodeTextLabel').value;
    nodes.update({id: currentNodeId, label: newLabel});
    document.getElementById('editPanel').style.display = 'none';
    var graphData = {
        nodes: nodes.get(),
        edges: edges.get()
    };
    document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
}

function cancelNodeChanges() {
    document.getElementById('editPanel').style.display = 'none';
}

function saveGraphData() {
    var graphData = {
        nodes: nodes.get(),
        edges: edges.get()
    };
    document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
    fetch('/save-graph', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(graphData)
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            alert('Graph saved successfully!');
        } else {
            alert('Failed to save graph.');
        }
    });
}

function loadPreviousGraph(graphId) {
    fetch(`/load-graph?graphId=${graphId}`)
        .then(response => response.json())
        .then(data => {
            if (data.nodes && data.edges) {
                nodes.clear();
                edges.clear();
                nodes.add(data.nodes);
                edges.add(data.edges);
                document.getElementById('jsonData').value = JSON.stringify({
                    nodes: data.nodes,
                    edges: data.edges
                }, null, 2);
            } else {
                alert('No data found.');
            }
        })
        .catch(error => {
            console.error('Error loading graph:', error);
            alert('Failed to load graph data.');
        });
}

var container = document.getElementById('mynetwork');
var data = {
    nodes: nodes,
    edges: edges
};
var options = {
    manipulation: {
        enabled: true,
        initiallyActive: true,
        editNode: editNodeFunction,
        addNode: function (nodeData, callback) {
            nodeData.label = "New Node";
            callback(nodeData);
        }
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
var network = new vis.Network(container, data, options);

function updatePhysics() {
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
    network.setOptions(newOptions);
}

function updateGraphFromJSON() {
    var jsonData = document.getElementById('jsonData').value;
    try {
        var graphData = JSON.parse(jsonData);
        nodes.clear();
        edges.clear();
        nodes.add(graphData.nodes);
        edges.add(graphData.edges);
    } catch (error) {
        alert('Invalid JSON format.');
    }
}

function resetJSON() {
    var graphData = {
        nodes: nodes.get(),
        edges: edges.get()
    };
    document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
}
