Tell-A-Scope
---


Python Library for Talking to Telescopes (and their components)

First order of business: Write interface for Meade LX200GPS

Layout:

	core:

		Core componenets, serial interface and hardware interaction happen here

	mantel:

		Abstracted core methods and classes that are usable to an end-user

	astro:

		Various astronomical tools

	virtual:

		Virutal hardware, things like auto-star II controller or custom telescope controllers

	UI:
	
		User interface scripts/front end

Feel free to update this README with suggested changes to layout below:

* Layout:

	* core:
		
		* telescope command set
		* telescope components (eyepieces, filters, cameras, etc)
		* telescope classes

	* mantel:
	
		* telescope classes (founded on core)

	* astro:

		* atmospheric data/corrections
		* object catalogs
		* telescope components (founded on core)
		* legacy object data access
		* stellarium interface?

	* virtual:

		* Autostar II Controller
		* Focuser Controller

	* UI:
	
		* curses UI
		* Qt/Tk UI

	*other:

