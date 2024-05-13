
function postToServer(command, data, callback)
{
    let endPoint = "http://34.135.217.92:8000/api/v1/commandHandler";
    //console.log(endPoint);
    
    let payloadObject = {
    command: command,
    data: data
    };

    const reqParams = {
    	method: 'POST',
    	headers: {
    	    'Content-type': 'application/json'
    	},
    	body: JSON.stringify(payloadObject)
    };

    console.log(reqParams);


    fetch(endPoint, reqParams)
	.then(response => response.json())
	.then(response => callback(response))
    //.catch(error => console.log(response));
    //.catch(error => console.log('Request failed', error));
	.catch(response => callback({'responseCode': '-2'}));
    return true;
}		
