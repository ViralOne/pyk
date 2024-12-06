$(document).ready(function() {
    // Utility function to sanitize strings before inserting into HTML
    function sanitize(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    const originalCallbacks = {
        configmaps: $.get,
        secrets: $.get,
        services: $.get,
        ingresses: $.get,
        events: $.get
    };

    // Load health status
    $.get(`/api/health/${namespace}`, function(data) {
        const table = $('#healthTable table');
        const loading = $('#healthTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        data.forEach(pod => {
            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(pod.name)}</td>
                    <td class="px-4 py-2">
                        <span class="px-2 py-1 text-xs rounded-full ${
                            pod.status === 'Running' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' :
                            pod.status === 'Pending' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100' :
                            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
                        }">${sanitize(pod.status)}</span>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(pod.cpu || 'N/A')}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(pod.memory || 'N/A')}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(pod.restarts)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(pod.age)}</td>
                    <td class="px-4 py-2">
                        <div class="flex items-center gap-2">
                            <button onclick="showPodDetails('${sanitize(pod.name)}')" 
                                    class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200">
                                <i class="fas fa-info-circle"></i>
                            </button>
                            <button class="debug-btn text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200"
                                    data-resource-type="pod"
                                    data-resource-name="${sanitize(pod.name)}">
                                <i class="fas fa-bug"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
        addDebugHandlers();
    });

    // Load images
    $.get(`/api/images/${namespace}`, function(data) {
        const table = $('#imagesTable table');
        const loading = $('#imagesTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        data.forEach(item => {
            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(item.pod_name)}</td>
                    <td class="px-4 py-2 text-sm font-mono text-gray-900 dark:text-white">${sanitize(item.image)}</td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
    });

    // Load configmaps
    $.get(`/api/configmaps/${namespace}`, function(data) {
        const table = $('#configMapsTable table');
        const loading = $('#configMapsTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        if (data.length === 0) {
            loading.html(`
                <div class="text-center text-gray-500 dark:text-gray-400">
                    <i class="fas fa-info-circle text-2xl mb-2"></i>
                    <p>No configmaps found</p>
                </div>
            `);
            return;
        }

        data.forEach(configmap => {
            const keys = configmap.data ? Object.keys(configmap.data) : [];
            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2">
                        <div class="flex items-center gap-2">
                            <span class="text-sm text-gray-900 dark:text-white">${sanitize(configmap.name)}</span>
                            <button class="debug-btn text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200"
                                    data-resource-type="configmap"
                                    data-resource-name="${sanitize(configmap.name)}">
                                <i class="fas fa-bug"></i>
                            </button>
                        </div>
                    </td>
                    <td class="px-4 py-2">
                        <div class="flex flex-wrap gap-1">
                            ${keys.map(key => `
                                <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                                    ${sanitize(key)}
                                </span>
                            `).join('')}
                        </div>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(configmap.age)}</td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
        addDebugHandlers();
    }).fail(function() {
        const table = $('#configMapsTable table');
        const loading = $('#configMapsTable .loading');
        loading.html(`
            <div class="text-center text-red-500">
                <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                <p>Failed to load configmaps</p>
            </div>
        `);
    });

    // Load secrets
    $.get(`/api/secrets/${namespace}`, function(data) {
        const table = $('#secretsTable table');
        const loading = $('#secretsTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        data.forEach(secret => {
            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2">
                        <div class="flex items-center gap-2">
                            <span class="text-sm text-gray-900 dark:text-white">${sanitize(secret.name)}</span>
                            <button class="debug-btn text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200"
                                    data-resource-type="secret"
                                    data-resource-name="${sanitize(secret.name)}">
                                <i class="fas fa-bug"></i>
                            </button>
                        </div>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(secret.type)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(secret.age)}</td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
        addDebugHandlers();
    });

    // Load services
    $.get(`/api/services/${namespace}`, function(data) {
        const table = $('#servicesTable table');
        const loading = $('#servicesTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        if (data.length === 0) {
            loading.html(`
                <div class="text-center text-gray-500 dark:text-gray-400">
                    <i class="fas fa-info-circle text-2xl mb-2"></i>
                    <p>No services found</p>
                </div>
            `);
            return;
        }

        data.forEach(service => {
            // Get external IP based on service type and status
            let externalIP = '';
            if (service.type === 'LoadBalancer') {
                if (service.status && service.status.loadBalancer && service.status.loadBalancer.ingress && service.status.loadBalancer.ingress.length > 0) {
                    const ingress = service.status.loadBalancer.ingress[0];
                    externalIP = ingress.ip || ingress.hostname || '<pending>';
                } else {
                    externalIP = '<pending>';
                }
            } else if (service.type === 'NodePort') {
                externalIP = 'Use node IP';
            } else if (service.type === 'ExternalName') {
                externalIP = service.externalName || '-';
            } else {
                externalIP = '-';
            }

            // Format ports array into readable string
            const formattedPorts = service.ports.map(port => {
                if (typeof port === 'object') {
                    return `${port.port}${port.protocol ? '/' + port.protocol : ''}${port.targetPort ? ' → ' + port.targetPort : ''}`;
                }
                return port;
            });

            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2">
                        <div class="flex items-center gap-2">
                            <span class="text-sm text-gray-900 dark:text-white">${sanitize(service.name)}</span>
                            <button class="debug-btn text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200"
                                    data-resource-type="service"
                                    data-resource-name="${sanitize(service.name)}">
                                <i class="fas fa-bug"></i>
                            </button>
                        </div>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(service.type || 'ClusterIP')}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(service.clusterIP || 'None')}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(externalIP)}</td>
                    <td class="px-4 py-2">
                        <div class="flex flex-wrap gap-1">
                            ${formattedPorts.map(port => `
                                <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                                    ${sanitize(port)}
                                </span>
                            `).join('')}
                        </div>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(service.age)}</td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
        addDebugHandlers();
    }).fail(function() {
        loading.html(`
            <div class="text-center text-red-500">
                <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                <p>Failed to load services</p>
            </div>
        `);
    });

    // Load ingresses
    $.get(`/api/ingresses/${namespace}`, function(data) {
        const container = $('#ingressesTable .grid');
        const loading = $('#ingressesTable .loading');
        container.empty();
        
        if (data.length === 0) {
            container.html(`
                <div class="text-center text-gray-500 dark:text-gray-400">
                    <i class="fas fa-info-circle text-2xl mb-2"></i>
                    <p>No ingresses found</p>
                </div>
            `);
        } else {
            data.forEach(ingress => {
                container.append(`
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-medium text-gray-900 dark:text-white">${sanitize(ingress.name)}</span>
                                <button class="debug-btn text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200"
                                        data-resource-type="ingress"
                                        data-resource-name="${sanitize(ingress.name)}">
                                    <i class="fas fa-bug"></i>
                                </button>
                            </div>
                            <span class="text-sm text-gray-500">${sanitize(ingress.age)}</span>
                        </div>
                        <div class="space-y-2">
                            ${ingress.rules ? ingress.rules.map(rule => `
                                <div class="bg-white dark:bg-gray-800 rounded p-3">
                                    <div class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                                        ${sanitize(rule.host || 'No host specified')}
                                    </div>
                                    <div class="space-y-1">
                                        ${rule.paths ? rule.paths.map(path => `
                                            <div class="flex items-center justify-between text-sm">
                                                <span class="text-gray-600 dark:text-gray-400">${sanitize(path.path || '/')}</span>
                                                <span class="text-gray-900 dark:text-white">${sanitize(typeof path.service === 'object' ? path.service.name : path.service)}</span>
                                            </div>
                                        `).join('') : '<div class="text-sm text-gray-500">No paths defined</div>'}
                                    </div>
                                </div>
                            `).join('') : '<div class="text-sm text-gray-500">No rules defined</div>'}
                        </div>
                    </div>
                `);
            });
        }

        loading.addClass('hidden');
        container.removeClass('hidden');
    });

    // Load events
    $.get(`/api/events/${namespace}`, function(data) {
        const table = $('#eventsTable table');
        const loading = $('#eventsTable .loading');
        const tbody = table.find('tbody');
        tbody.empty();

        data.forEach(event => {
            tbody.append(`
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-2">
                        <span class="px-2 py-1 text-xs rounded-full ${
                            event.type === 'Normal' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' :
                            'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100'
                        }">${sanitize(event.type)}</span>
                    </td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(event.reason)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(event.object)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(event.message)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(event.count)}</td>
                    <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">${sanitize(event.last_seen)}</td>
                </tr>
            `);
        });

        loading.addClass('hidden');
        table.removeClass('hidden');
    });
});
