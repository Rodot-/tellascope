Tell-A-Scope
---


Python Library for Talking to Telescopes (and their components)

First order of business: Write interface for Meade LX200GPS

Layout:

	* core:

		Core componenets, serial interface and hardware interaction happen here

	* mantel:

		Abstracted core methods and classes that are usable to an end-user

	* astro:

		Various astronomical tools

	* virtual:

		Virutal hardware, things like auto-star II controller or custom telescope controllers

	* UI:
	
		User interface scripts/front end

