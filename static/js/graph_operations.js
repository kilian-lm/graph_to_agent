// Setup vis.js network datasets for nodes and edges
var nodes = new vis.DataSet();
var edges = new vis.DataSet();
var currentNodeId;

// Function to update the JSON view and the graph with the provided graph data
function updateGraph(graphData) {
  nodes.clear();
  edges.clear();
  nodes.add(graphData.nodes);
  edges.add(graphData.edges);
  saveEntireGraphToJSON(); // Update the JSON view with the entire graph
  console.log('Graph updated:', graphData);
}

// Function to update the JSON view with the entire graph
function saveEntireGraphToJSON() {
  var graphData = {
    nodes: nodes.get(),
    edges: edges.get()
  };
  document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
}

// Event listener for graph selection dropdown
document.getElementById('graphDropdown').addEventListener('change', async function () {
  const selectedGraphId = this.value;
  console.log('Graph dropdown changed:', selectedGraphId);
  if (selectedGraphId) {
    try {
      const response = await fetch('/get-graph-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          graph_id: selectedGraphId
        })
      });
      const graphData = await response.json();
      updateGraph(graphData); // Use the new updateGraph function to update the graph
      console.log('Graph data loaded:', graphData);
    } catch (error) {
      console.error('Error loading graph data:', error);
    }
  }
});

// Load available graphs for selection
async function loadAvailableGraphs() {
  console.log('Loading available graphs...');
  try {
    const response = await fetch('/get-available-graphs');
    const graphs = await response.json();
    const dropdown = document.getElementById('graphDropdown');
    dropdown.innerHTML = ''; // Clear the dropdown before adding new options
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

// Initial call to load available graphs
loadAvailableGraphs();


// Function to handle node editing
function editNodeFunction(nodeData, callback) {
    currentNodeId = nodeData.id;
    document.getElementById('nodeTextLabel').value = nodeData.label;
    document.getElementById('editPanel').style.display = 'block';
    console.log('Editing node:', currentNodeId);
}

// Function to apply changes to an edited node
function applyNodeChanges() {
    var newLabel = document.getElementById('nodeTextLabel').value;
    nodes.update({id: currentNodeId, label: newLabel});
    document.getElementById('editPanel').style.display = 'none';
    saveEntireGraphToJSON(); // Update the JSON view with the entire graph
    network.setOptions({manipulation: {initiallyActive: true}}); // Reactivate manipulation GUI
    console.log('Node changes applied:', currentNodeId, newLabel);
}

// Function to cancel node edits
function cancelNodeChanges() {
    document.getElementById('editPanel').style.display = 'none';
    saveEntireGraphToJSON(); // Update the JSON view with the entire graph
    network.setOptions({manipulation: {initiallyActive: true}}); // Reactivate manipulation GUI
    console.log('Node changes canceled:', currentNodeId);
}


function saveGraphData() {
    var graphData = {
        nodes: nodes.get(),
        edges: edges.get()
    };
    document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
    console.log('Saving graph data:', graphData);
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

var container = document.getElementById('graph');
var data = {
    nodes: nodes,
    edges: edges
};
var options = {
    manipulation: {
        enabled: true,
        initiallyActive: true,
            multiselect: true,

        editNode: editNodeFunction,
        // Ensure to update JSON view after adding a node
        addNode: function (nodeData, callback) {
            nodeData.label = "New Node";
            callback(nodeData);
            saveEntireGraphToJSON(); // Update the JSON view with the entire graph
            console.log('New node added:', nodeData);
        },
        // Ensure to update JSON view after deleting a node
        deleteNode: function (nodeData, callback) {
            callback(nodeData);
            saveEntireGraphToJSON(); // Update the JSON view with the entire graph
            console.log('Node deleted:', nodeData);
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
    console.log('Physics updated:', newOptions);
}


function updateGraphFromJSON() {
    var jsonData = document.getElementById('jsonData').value;
    try {
        var graphData = JSON.parse(jsonData);
        nodes.clear();
        edges.clear();
        nodes.add(graphData.nodes);
        edges.add(graphData.edges);
        console.log('Graph updated from JSON:', graphData);
    } catch (error) {
        alert('Invalid JSON format.');
        console.error('Invalid JSON format:', error);
    }
}

function resetJSON() {
    var graphData = {
        nodes: nodes.get(),
        edges: edges.get()
    };
    document.getElementById('jsonData').value = JSON.stringify(graphData, null, 2);
    console.log('JSON reset:', graphData);
}

// Assuming 'network' is your vis.Network instance
network.on("select", function (params) {
  console.log('Selected nodes:');
  console.log(params.nodes);

  console.log('Selected edges:');
  console.log(params.edges);

  // You can now perform actions on the selected nodes and edges
});

async function gptPostRequest() {
  var graphData = {
    nodes: nodes.get(),
    edges: edges.get()
  };

  console.log('Graph data being sent to backend:', graphData);

  // try {
  const response = await fetch('/return-gpt-agent-answer-to-graph', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(graphData)
  });

  const data = await response.json();

  // if (data.status === 'success') {
  updateGraph(data.updatedGraph); // Use the new updateGraph function to update the graph
  //     } else {
  //         console.error('Failed to process GPT request:', data);
  //         alert('Failed to process GPT request.');
  //     }
  // } catch (error) {
  //     console.error('Error in GPT request:', error);
  //     alert('An error occurred while processing the GPT request.');
  // }
}