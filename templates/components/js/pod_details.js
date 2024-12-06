function showPodDetails(podName) {
    const modal = $('#podDetailsModal');
    const modalContent = $('#modalContent');
    const modalPodName = $('#modalPodName');
    
    modal.removeClass('hidden');
    modalPodName.text(podName);
    modalContent.html(`
        <div class="flex items-center justify-center p-8 text-gray-500 dark:text-gray-400">
            <i class="fas fa-spinner fa-spin text-2xl"></i>
        </div>
    `);
    
    $.get(`/api/pods/${namespace}/${podName}`)
        .done(function(data) {
            let html = '';
            
            // Status Section
            html += `
                <div class="mb-6">
                    <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</h3>
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="w-2 h-2 rounded-full ${
                                data.status === 'Running' ? 'bg-green-500' :
                                data.status === 'Pending' ? 'bg-yellow-500' :
                                'bg-red-500'
                            }"></span>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">${data.status}</span>
                        </div>
                        ${data.status_message ? `
                            <p class="text-sm text-gray-600 dark:text-gray-400">${data.status_message}</p>
                        ` : ''}
                    </div>
                </div>
            `;
            
            // Details Section
            html += `
                <div class="mb-6">
                    <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Details</h3>
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 space-y-2">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <span class="text-xs text-gray-500 dark:text-gray-400">Node</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">${data.node || 'N/A'}</p>
                            </div>
                            <div>
                                <span class="text-xs text-gray-500 dark:text-gray-400">IP</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">${data.pod_ip || 'N/A'}</p>
                            </div>
                            <div>
                                <span class="text-xs text-gray-500 dark:text-gray-400">Created</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">${data.created_at || 'N/A'}</p>
                            </div>
                            <div>
                                <span class="text-xs text-gray-500 dark:text-gray-400">Restarts</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">${data.restart_count || '0'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Containers Section
            if (data.containers && data.containers.length > 0) {
                html += `
                    <div class="mb-6">
                        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Containers</h3>
                        <div class="space-y-3">
                `;
                
                data.containers.forEach(container => {
                    html += `
                        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">${container.name}</span>
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    container.ready ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' :
                                    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100'
                                }">${container.ready ? 'Ready' : 'Not Ready'}</span>
                            </div>
                            <div class="space-y-1 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-600 dark:text-gray-400">Image:</span>
                                    <span class="text-gray-900 dark:text-white font-mono">${container.image}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600 dark:text-gray-400">State:</span>
                                    <span class="text-gray-900 dark:text-white">${container.state || 'Unknown'}</span>
                                </div>
                                ${container.state_message ? `
                                    <div class="text-gray-600 dark:text-gray-400 mt-2">
                                        ${container.state_message}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            // Events Section
            if (data.events && data.events.length > 0) {
                html += `
                    <div>
                        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Recent Events</h3>
                        <div class="space-y-2">
                `;
                
                data.events.forEach(event => {
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
            }
            
            modalContent.html(html);
        })
        .fail(function(error) {
            modalContent.html(`
                <div class="text-center text-red-500">
                    <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                    <p>Failed to load pod details</p>
                </div>
            `);
        });
    
    // Close modal when clicking outside or on close button
    modal.find('.close-modal').off('click').on('click', function() {
        modal.addClass('hidden');
    });
    
    $(document).off('click.modal').on('click.modal', function(e) {
        if ($(e.target).is(modal)) {
            modal.addClass('hidden');
        }
    });
}
