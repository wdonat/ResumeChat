
	//----------------------------
	//- Authentication functions -
	//----------------------------
	
	var auth_loggedUserInfo = null;

	function auth_loginUserWithCredentials(username, password)
	{
		
		let command = "login";

		let data = 
		{
			username: username,
			password: password
		};

		postToServer(command, data, auth_processLoginResponse);

	    return true;
	}

	function auth_processLoginResponse(response)
	{
	    if (response.responseCode === "1")
	    {
			console.log("Logged in successfullly!");
			window.location.href = "index.html";
	    }
		else if(response.responseCode === "-1")
		{
			alertCustom("An error has occurred:\n"+response.responseMessage);
		}
		else
		{
			alertCustom("An unexpected error has occurred!")
		}
	}

	function auth_getLoggedInUserInfo(boolRedirectToLogin=true, funcOnSuccess=null, funcOnFailure=null)
	{
		postToServer("getLoggedInUserInfo", { }, (response) => { auth_processGetLoggedInUserInfoResponse(response, boolRedirectToLogin, funcOnSuccess, funcOnFailure); });
	}

	function auth_processGetLoggedInUserInfoResponse(response, boolRedirectToLogin=true, funcOnSuccess=null, funcOnFailure=null)
	{
		if(response.responseCode === "1")
		{
			auth_loggedUserInfo = auth_convertServerLoggedInUserResponseToLocalData(response.data);
			
			if(funcOnSuccess != null)
			{
				funcOnSuccess();
			}
		}
		else if(response.responseCode === "-1")
		{
			if(boolRedirectToLogin)
			{
				window.location.href = "login.html";
			}
			else if(funcOnFailure != null)
			{
				funcOnFailure();
			}
		}
		else
		{
			alertCustom("An authentication error has occurred!")
		}
	}


	function auth_convertServerLoggedInUserResponseToLocalData(response)
	{
		let localData = 
		{
			id: response.user_id,
			name: response.name,
			username: response.username,
			type: response.type
		};
		
		return localData;
	}

	function auth_logout()
	{
		postToServer("logout", {}, auth_processLogoutResponse);

	    return true;
	}


	function auth_processLogoutResponse(response)
	{
	    if(response.responseCode === "1")
	    {
	    	auth_getLoggedInUserInfo(true, () => { });
	    }

		else if(response.responseCode === "-1")
		{
			alertCustom("An error has occurred:\n"+response.responseMessage)
		}

		else
		{
			alertCustom("An unexpected error has occurred!")
		}
	}
