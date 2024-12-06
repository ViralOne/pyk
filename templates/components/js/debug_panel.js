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
