const DEF_API_VERSION = '0.1';

class AdapterEndpoint 
{
    constructor(adapter, api_version=DEF_API_VERSION) 
    {
        this.adapter = adapter;
        this.api_version = api_version;
    }

    build_url(path)
    {
        return `api/${this.api_version}/${this.adapter}/${path}`;
    }

    async get(path='', timeout=8000) 
    {
        const abort_controller = new AbortController();
        const abort_promise = setTimeout(() => abort_controller.abort(), timeout);

        const url = this.build_url(path);
        const response = await fetch(
            url,
            { 
                method: 'GET',
                headers: {'Accept': 'application/json'},
                signal: abort_controller.signal
            }
        )
        .catch(error => {
            if (error.name == 'AbortError') {
                throw new Error(`GET request to ${url} timed out after ${timeout}ms`);
            }
            else {
                throw error;
            }
        });

        clearTimeout(abort_promise);

        if (!response.ok) {
            var message;
            try {
                const err_result = await response.json();
                message = err_result.error;
            }
            catch
            {
                message = `GET request to ${url} failed with status ${response.status}`;  
            }
            throw new Error(message);
        }
        const result = await response.json();
        return result;
    }

    async put(data, path='', timeout=8000)
    {
        const abort_controller = new AbortController();
        const abort_promise = setTimeout(() => abort_controller.abort(), timeout);

        const url = this.build_url(path);
        const response = await fetch(
            url,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data),
                signal: abort_controller.signal
            }
        )
        .catch(error => {
            if (error.name == 'AbortError') {
                throw new Error(`PUT request to ${url} timed out after ${timeout}ms`);
            }
            else {
                throw error;
            }
        });

        clearTimeout(abort_promise);

        if (!response.ok) {
            var message;
            try {
                const err_result = await response.json();
                message = err_result.error;
            }
            catch
            {
                message = `PUT request to ${url} failed with status ${response.status}`;
            }
            throw new Error(message);
        }
        const result = await response.json();
        return result;
    }

}
