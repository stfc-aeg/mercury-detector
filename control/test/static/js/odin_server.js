var api_version = '0.1';
var adapter = 'odin_sequencer';

/**
 * This function handles the GET requests to the backend's API. 
 */
function apiGET(path) {
    return $.ajax({
        url: `api/${api_version}/${adapter}/${path}`,
        type: 'GET',
        dataType: 'json'
    });
}

/**
 * This function handles the API requests to the backend's API.
 */
function apiPUT(data, path='') {
    return $.ajax({
        url: `api/${api_version}/${adapter}/${path}`,
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(data)
    });
}
