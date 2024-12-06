function closeDebugPanel() {
    $('#debugPanel').addClass('hidden');
}

function showDebugPanel(resourceType, resourceName) {
    const debugPanel = $('#debugPanel');
    const resourceDetails = $('#debugResourceDetails');
    const relatedResources = $('#debugRelatedResources');
    
    debugPanel.removeClass('hidden');
    
    // Show loading state
    resourceDetails.html(`
        <div class="animate-pulse">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
    `);
    
    relatedResources.html(`
        <div class="animate-pulse">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
    `);
    
    // Fetch resource details and relationships
    $.get(`/api/debug/${resourceType}/${namespace}/${resourceName}`)
        .done(function(data) {
            // Resource Details
            let detailsHtml = generateResourceDetailsHtml(data);
            resourceDetails.html(detailsHtml);
            
            // Related Resources
            let relatedHtml = generateRelatedResourcesHtml(data);
            relatedResources.html(relatedHtml);

            // Initialize Service Graph
            initializeServiceGraph(data);
        })
        .fail(function(error) {
            resourceDetails.html(`
                <div class="text-red-500">
                    <i class="fas fa-exclamation-circle"></i>
                    Failed to load resource details
                </div>
            `);
            relatedResources.html(`
                <div class="text-red-500">
                    <i class="fas fa-exclamation-circle"></i>
                    Failed to load related resources
                </div>
            `);
        });
}

function generateResourceDetailsHtml(data) {
    let html = `
        <div class="mb-4">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Resource Info</h4>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <div class="flex items-center gap-2 mb-2">
                    <span class="text-sm font-medium text-gray-900 dark:text-white">${data.type}</span>
                    <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                        ${data.name}
                    </span>
                </div>
                <div class="space-y-2">
    `;
    
    Object.entries(data.details).forEach(([key, value]) => {
        if (key !== 'type' && key !== 'name') {
            html += `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600 dark:text-gray-400">${key}:</span>
                    <span class="text-gray-900 dark:text-white font-mono">${Array.isArray(value) ? value.join(', ') : value}</span>
                </div>
            `;
        }
    });
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    if (data.events && data.events.length > 0) {
        html += generateEventsHtml(data.events);
    }
    
    return html;
}

function generateEventsHtml(events) {
    let html = `
        <div>
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Events</h4>
            <div class="space-y-2">
    `;
    
    events.forEach(event => {
        html += `
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-2 text-sm">
                <div class="flex items-center gap-2 mb-1">
                    <span class="w-2 h-2 rounded-full ${event.type === 'Normal' ? 'bg-green-500' : 'bg-yellow-500'}"></span>
                    <span class="font-medium text-gray-900 dark:text-white">${event.reason}</span>
                </div>
                <p class="text-gray-600 dark:text-gray-400">${event.message}</p>
                <div class="mt-1 text-xs text-gray-500">
                    Count: ${event.count} | Last seen: ${event.last_timestamp}
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    return html;
}

function generateRelatedResourcesHtml(data) {
    let html = `
        <div class="space-y-4">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Related Resources</h4>
    `;
    
    Object.entries(data.related).forEach(([type, resources]) => {
        if (resources.length > 0) {
            html += `
                <div>
                    <h5 class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">${type}</h5>
                    <div class="space-y-2">
            `;
            
            resources.forEach(resource => {
                html += `
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                         onclick="showDebugPanel('${type.toLowerCase().slice(0, -1)}', '${resource.name}')">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">${resource.name}</span>
                                ${resource.status ? `
                                    <span class="px-2 py-1 text-xs rounded-full ${
                                        resource.status === 'Healthy' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' :
                                        resource.status === 'Warning' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100' :
                                        'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                                    }">${resource.status}</span>
                                ` : ''}
                            </div>
                            <i class="fas fa-chevron-right text-gray-400"></i>
                        </div>
                        ${resource.info ? `
                            <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">${resource.info}</div>
                        ` : ''}
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
    });
    
    html += `</div>`;
    return html;
}

function addDebugHandlers() {
    // Add click handlers for debug buttons
    $('.debug-btn').off('click').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const resourceType = $(this).data('resource-type');
        const resourceName = $(this).data('resource-name');
        showDebugPanel(resourceType, resourceName);
    });
}

function switchDebugTab(tabName) {
    // Update tab buttons
    $('.debug-tab').removeClass('active bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white')
        .addClass('text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800');
    
    $(`.debug-tab[data-tab="${tabName}"]`)
        .addClass('active bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white')
        .removeClass('text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800');
    
    // Update tab panels
    $('.debug-tab-panel').addClass('hidden').removeClass('active');
    $(`#${tabName}Tab`).removeClass('hidden').addClass('active');
    
    // If switching to graph tab, resize the network to fit
    if (tabName === 'graph') {
        resizeGraph();
    }
}

// Service Graph Module
let networkInstance = null;

function initializeServiceGraph(data) {
    console.log('Initializing service graph with data:', data);
    
    if (!data) {
        console.log('No data found');
        return;
    }

    const container = document.getElementById('serviceGraph');
    if (!container) {
        console.error('Service graph container not found');
        return;
    }

    // Clear any existing network
    if (networkInstance) {
        networkInstance.destroy();
        networkInstance = null;
    }

    // Ensure container is visible and has dimensions
    container.style.height = '400px';
    container.style.width = '100%';
    
    const nodes = new Set();
    const edges = new Set();
    const nodeGroups = {
        current: { color: '#3B82F6', title: 'Current Service' },
        service: { color: '#F59E0B', title: 'Service' },
        pod: { color: '#10B981', title: 'Pod' },
        ingress: { color: '#8B5CF6', title: 'Ingress' },
        configmap: { color: '#6B7280', title: 'ConfigMap' },
        secret: { color: '#EF4444', title: 'Secret' }
    };

    // Helper function to add a node
    function addNode(id, label, groupKey, extraData = {}) {
        try {
            // Check if node already exists
            const existingNodes = Array.from(nodes);
            if (existingNodes.some(node => node.id === id)) {
                console.log(`Node ${id} already exists, skipping...`);
                return;
            }

            const group = nodeGroups[groupKey];
            if (!group) {
                console.warn(`Unknown group key: ${groupKey} for node ${id}`);
                return;
            }

            nodes.add({
                id,
                label: label || id,
                color: group.color,
                group: groupKey,
                title: group.title
            });
        } catch (error) {
            console.error(`Error adding node ${id}:`, error);
        }
    }

    // Helper function to add an edge
    function addEdge(from, to, type = 'service') {
        try {
            // Check if edge already exists
            const existingEdges = Array.from(edges);
            if (existingEdges.some(edge => edge.from === from && edge.to === to)) {
                console.log(`Edge from ${from} to ${to} already exists, skipping...`);
                return;
            }

            const group = nodeGroups[type];
            if (!group) {
                console.warn(`Unknown edge type: ${type}`);
                return;
            }

            edges.add({
                from,
                to,
                arrows: 'to',
                color: { color: group.color, opacity: 0.6 }
            });
        } catch (error) {
            console.error(`Error adding edge from ${from} to ${to}:`, error);
        }
    }

    // Add current service/resource node with its type
    addNode(data.name, data.name, data.type.toLowerCase(), data.details || {});

    // Process related resources
    if (data.related) {

        // Add Pods
        if (data.related.Pods) {
            data.related.Pods.forEach(pod => {
                addNode(pod.name, pod.name, 'pod', pod);
                addEdge(data.name, pod.name, 'pod');
            });
        }

        // Add Ingresses
        if (data.related.Ingresses) {
            data.related.Ingresses.forEach(ingress => {
                addNode(ingress.name, ingress.name, 'ingress', ingress);
                addEdge(ingress.name, data.name, 'ingress');
            });
        }

        // Add Services
        if (data.related.Services) {
            data.related.Services.forEach(service => {
                addNode(service.name, service.name, 'service', service);
                addEdge(data.name, service.name, 'service');
            });
        }

        // Add ConfigMaps
        if (data.related.ConfigMaps) {
            data.related.ConfigMaps.forEach(cm => {
                addNode(cm.name, cm.name, 'configmap', cm);
                addEdge(data.name, cm.name, 'configmap');
            });
        }

        // Add Secrets
        if (data.related.Secrets) {
            data.related.Secrets.forEach(secret => {
                addNode(secret.name, secret.name, 'secret', secret);
                addEdge(data.name, secret.name, 'secret');
            });
        }
    }

    // Process service graph data if available (for backward compatibility)
    if (data.graph) {
        // Add service dependencies
        if (data.graph.dependencies) {
            data.graph.dependencies.forEach(dep => {
                addNode(dep.name, dep.name, 'service', dep);
                addEdge(data.name, dep.name, 'service');
            });
        }

        // Add services depending on this one
        if (data.graph.dependents) {
            data.graph.dependents.forEach(dep => {
                addNode(dep.name, dep.name, 'service', dep);
                addEdge(dep.name, data.name, 'service');
            });
        }

        // Add service connections (bidirectional relationships)
        if (data.graph.connections) {
            data.graph.connections.forEach(conn => {
                addNode(conn.name, conn.name, 'service', conn);
                // Add bidirectional edge
                addEdge(data.name, conn.name, 'service');
                addEdge(conn.name, data.name, 'service');
            });
        }
    }

    const options = {
        nodes: {
            shape: 'dot',
            size: 16,
            font: {
                size: 12,
                color: '#374151'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'horizontal',
                roundness: 0.4
            }
        },
        layout: {
            hierarchical: {
                enabled: true,
                direction: 'LR',
                sortMethod: 'directed',
                nodeSpacing: 150,
                levelSeparation: 200
            }
        },
        physics: {
            enabled: false
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
            tooltipDelay: 100,
            hideEdgesOnDrag: true
        },
        groups: Object.fromEntries(
            Object.entries(nodeGroups).map(([key, value]) => [
                key,
                { color: { background: value.color, border: value.color } }
            ])
        )
    };

    try {
        // Create the network
        networkInstance = new vis.Network(container, {
            nodes: new vis.DataSet(Array.from(nodes)),
            edges: new vis.DataSet(Array.from(edges))
        }, options);

        // Handle node clicks
        networkInstance.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const resourceTypes = {
                    'pod': data.related?.Pods,
                    'ingress': data.related?.Ingresses,
                    'service': [...(data.related?.Services || []), 
                              ...(data.graph?.dependencies || []),
                              ...(data.graph?.dependents || []),
                              ...(data.graph?.connections || [])],
                    'configmap': data.related?.ConfigMaps,
                    'secret': data.related?.Secrets
                };

                for (const [type, resources] of Object.entries(resourceTypes)) {
                    const resource = resources?.find(r => r.name === nodeId);
                    if (resource) {
                        window.showDebugPanel(type, resource.name);
                        break;
                    }
                }
            }
        });

        // Fit the network to the container after a short delay
        setTimeout(() => networkInstance.fit(), 250);
    } catch (error) {
        console.error('Error creating network:', error);
    }
}

function resizeGraph() {
    if (networkInstance) {
        networkInstance.fit();
    }
}
