
	//---------------------
	//- Utility functions -
	//---------------------

	function getRadioValue(group)
	{
		for (var i=0; i < group.length; i++)
		{
			if (group[i].checked)
			{
				return(group[i].value);
			}
		}

		return "";
	}
	
	function setRadioValue(group, selectedItem)
	{
		for (var i=0; i < group.length; i++)
		{
			if (group[i].value == selectedItem)
			{
				group[i].checked = true;
				return true;
			}
		}

		return false;
	}

	function toTitleCase(str)
	{
		str = str.toLowerCase().split(' ');
		
		for (var i = 0; i < str.length; i++)
		{
			str[i] = str[i].charAt(0).toUpperCase() + str[i].slice(1);
		}

		return str.join(' ');
	};

	function countDecimals(num)
	{
		if(Math.floor(num.valueOf()) === num.valueOf())
		{
			return 0;
		}

		return num.toString().split(".")[1].length || 0; 
	}


