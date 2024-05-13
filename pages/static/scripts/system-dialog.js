
	// ------------------------
	// - System Dialog Handling
	// ------------------------
	
	var g_systemDialogType = "";
	var g_systemDialogFuncTrue = null;
	var g_systemDialogFuncFalse = null;

	function initSystemDialog(strRootDivId)
	{
		document.getElementById(strRootDivId).innerHTML += "<div id='divSystemDialog' class='systemDialog hidden'>"+
			" <div class='systemDialogContainer'>"+
			"  <div class='systemDialogTitleBar'>"+
			"   <img src='static/images/message_icon.png' class='systemDialogIcon' />"+
			"   <div class='systemDialogTitle'>System Message</div>"+
			"  </div>"+
			"  <div class='systemDialogBody'>"+
			"   <div id='divSystemDialogMessage' class='systemDialogMessage'>Text</div>"+
			"   <div class='systemDialogButtons'>"+
			"    <div id='divSystemDialogCancelButton' class='systemDialogButton red' onClick='clickedOnSystemDialogCancelButton();'>Cancel</div>"+
			"    <div id='divSystemDialogOkButton' class='systemDialogButton green' onClick='clickedOnSystemDialogOkButton();'>OK</div>"+
			"    <div id='divSystemDialogCloseButton' class='systemDialogButton green' onClick='clickedOnSystemDialogCancelButton();'>Close</div>"+
			"   </div>"+
			"  </div>"+
			" </div>"+
			"</div>";
	}
	
	function showSystemDialog()
	{
		document.getElementById("divSystemDialog").classList.remove("hidden");
	}

	function hideSystemDialog()
	{
		document.getElementById("divSystemDialog").classList.add("hidden");
	}

	function setSystemDialogMessage(message)
	{
		document.getElementById("divSystemDialogMessage").innerHTML = message.replace(/\n/g, "<br>");
	}

	function showSystemDialogCancelButton()
	{
		document.getElementById("divSystemDialogCancelButton").classList.remove("hidden");
	}

	function hideSystemDialogCancelButton()
	{
		document.getElementById("divSystemDialogCancelButton").classList.add("hidden");
	}

	function showSystemDialogCloseButton()
	{
		document.getElementById("divSystemDialogCloseButton").classList.remove("hidden");
	}

	function hideSystemDialogCloseButton()
	{
		document.getElementById("divSystemDialogCloseButton").classList.add("hidden");
	}

	function showSystemDialogOkButton()
	{
		document.getElementById("divSystemDialogOkButton").classList.remove("hidden");
	}

	function hideSystemDialogOkButton()
	{
		document.getElementById("divSystemDialogOkButton").classList.add("hidden");
	}
	
	function alertCustom(message)
	{
		g_systemDialogType = "ALERT";
		g_systemDialogFuncTrue = null;
		g_systemDialogFuncFalse = null;
		hideSystemDialogCancelButton();
		hideSystemDialogOkButton();
		showSystemDialogCloseButton();
		setSystemDialogMessage(message);
		showSystemDialog();
	}

	function confirmCustom(message, funcTrue, funcFalse)
	{
		g_systemDialogType = "CONFIRM";
		g_systemDialogFuncTrue = funcTrue;
		g_systemDialogFuncFalse = funcFalse;
		showSystemDialogCancelButton();
		showSystemDialogOkButton();
		hideSystemDialogCloseButton();
		setSystemDialogMessage(message);
		showSystemDialog();
	}
	
	function clickedOnSystemDialogCancelButton()
	{
		if(g_systemDialogType == "CONFIRM" && g_systemDialogFuncFalse != null)
		{
			g_systemDialogFuncFalse();
		}

		g_systemDialogType = "";
		g_systemDialogFuncTrue = null;
		g_systemDialogFuncFalse = null;
		hideSystemDialog();
	}

	function clickedOnSystemDialogOkButton()
	{
		if(g_systemDialogType == "CONFIRM" && g_systemDialogFuncTrue != null)
		{
			g_systemDialogFuncTrue();
		}
		
		g_systemDialogType = "";
		g_systemDialogFuncTrue = null;
		g_systemDialogFuncFalse = null;
		hideSystemDialog();
	}
