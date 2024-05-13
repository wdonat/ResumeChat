
function initCustomSelectElements(strClassName)
{
	let x, i, j, selElmnt, a, b, c;

	/*look for any elements with the class "custom-select":*/
	x = document.getElementsByClassName(strClassName);

	for (i = 0; i < x.length; i++)
	{
		selElmnt = x[i].getElementsByTagName("select")[0];

		/*for each element, create a new DIV that will act as the selected item:*/
		a = document.createElement("DIV");
		a.setAttribute("class", "select-selected");
		a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
		x[i].appendChild(a);

		/*for each element, create a new DIV that will contain the option list:*/
		let b = document.createElement("DIV");
		b.setAttribute("class", "select-items select-hide");
	
		for (j = 1; j < selElmnt.length; j++)
		{
			/*for each option in the original select element,
			create a new DIV that will act as an option item:*/
			c = document.createElement("DIV");
			c.innerHTML = selElmnt.options[j].innerHTML;
			c.value = selElmnt.options[j].value;

			c.addEventListener("click", function(e)
			{
				/*when an item is clicked, update the original select box,
				and the selected item:*/
				var y, i, k, s, h;
				s = this.parentNode.parentNode.getElementsByTagName("select")[0];
				h = this.parentNode.previousSibling;
		
				for (i = 0; i < s.length; i++)
				{
					if (s.options[i].innerHTML == this.innerHTML)
					{
						s.selectedIndex = i;
						h.innerHTML = this.innerHTML;
						y = this.parentNode.getElementsByClassName("same-as-selected");
	
						for (k = 0; k < y.length; k++)
						{
							y[k].removeAttribute("class");
						}
				
						this.setAttribute("class", "same-as-selected");
						break;
					}
				}
		
				h.click();
			});
	
			b.appendChild(c);
		}

		x[i].appendChild(b);

		a.addEventListener("click", function(e)
		{
			/*when the select box is clicked, close any other select boxes,
			and open/close the current select box:*/
			e.stopPropagation();
			closeAllSelect(this);
			this.nextSibling.classList.toggle("select-hide");
			this.classList.toggle("select-arrow-active");
		});
		
		x[i].selectOptionWithText = (text) =>
		{
			let y, i, k, s, h;
			let _this = null;
			
			let optionNodes = b.childNodes;
			
			for (i = 0; i < optionNodes.length; i++)
			{
				if(optionNodes[i].childNodes[0].wholeText == text)
				{
					_this = optionNodes[i];
				}
			}
			
			if(_this === null)
			{
				return;
			}
			
			s = _this.parentNode.parentNode.getElementsByTagName("select")[0];
			h = _this.parentNode.previousSibling;
		
			for (i = 0; i < s.length; i++)
			{
				if (s.options[i].innerHTML == _this.innerHTML)
				{
					s.selectedIndex = i;
					h.innerHTML = _this.innerHTML;
					y = _this.parentNode.getElementsByClassName("same-as-selected");
					
					for (k = 0; k < y.length; k++)
					{
						y[k].removeAttribute("class");
					}
			
					_this.setAttribute("class", "same-as-selected");
					break;
				}
			}
	
			h.click();
			closeAllSelect();
		}

		x[i].selectOptionWithValue = (val) =>
		{
			let y, i, k, s, h;
			let _this = null;
			
			let optionNodes = b.childNodes;
			
			for (i = 0; i < optionNodes.length; i++)
			{
				if(optionNodes[i].value == val)
				{
					_this = optionNodes[i];
				}
			}
			
			if(_this === null)
			{
				return;
			}
			
			s = _this.parentNode.parentNode.getElementsByTagName("select")[0];
			h = _this.parentNode.previousSibling;
		
			for (i = 0; i < s.length; i++)
			{
				if (s.options[i].innerHTML == _this.innerHTML)
				{
					s.selectedIndex = i;
					h.innerHTML = _this.innerHTML;
					y = _this.parentNode.getElementsByClassName("same-as-selected");
					
					for (k = 0; k < y.length; k++)
					{
						y[k].removeAttribute("class");
					}
			
					_this.setAttribute("class", "same-as-selected");
					break;
				}
			}
	
			h.click();
			closeAllSelect();
		}
/*
		Object.defineProperty(selElmnt, "value", 
		{
			get: () =>
			{
				return selElmnt.myValue;
			},
			set: (val) =>
			{
				selElmnt.myValue = val;
				selElmnt.parentNode.selectOptionWithValue(val);
			}
		});
*/
	}

	function closeAllSelect(elmnt)
	{
		/*a function that will close all select boxes in the document,
		except the current select box:*/
		var x, y, i, arrNo = [];
		x = document.getElementsByClassName("select-items");
		y = document.getElementsByClassName("select-selected");
	
		for (i = 0; i < y.length; i++)
		{
			if (elmnt == y[i])
			{
				arrNo.push(i)
			}
			else
			{
				y[i].classList.remove("select-arrow-active");
			}
		}

		for (i = 0; i < x.length; i++)
		{
			if (arrNo.indexOf(i))
			{
				x[i].classList.add("select-hide");
			}
		}
	}

	/*if the user clicks anywhere outside the select box,
	then close all select boxes:*/
	document.addEventListener("click", closeAllSelect);
}
