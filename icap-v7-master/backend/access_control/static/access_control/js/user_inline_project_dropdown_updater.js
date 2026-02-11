// This file contains the code that manages project permissions from the backend admin panel.

document.addEventListener("DOMContentLoaded", () => {
    const projectDropdownSelector = '.inline-related select[id$="-project"]'

    const updateProjectDropdowns = () => {
        const projectDropdowns = document.querySelectorAll(projectDropdownSelector)
        const selectedProjects = []

        // Listing all selected projects
        projectDropdowns.forEach(select => {
            if (select.value) {
                selectedProjects.push(select.value)
            }
        })

        // Disables selected projects throughout the dropdowns
        projectDropdowns.forEach(select => {
            const currentSelection = select.value
            const options = select.querySelectorAll('option')

            options.forEach(option => {
                if (option.value && !selectedProjects.includes(option.value)) {
                    option.disabled = false
                } else if (option.value && option.value !== currentSelection) {
                    option.disabled = true
                }
            })
        })
    }

    // Remove the '+' (add another) and pencil (change) buttons next to ForeignKey and ManyToManyField inputs
    const removeAddAndChangeButtons = () => {
        const addAndChangeButtons = document.querySelectorAll('.add-related, .change-related, .add-row a')

        addAndChangeButtons.forEach(btn => {
            btn.remove()
        })


        const projectDropdownWrapper = document.querySelectorAll('.related-widget-wrapper, .related-widget-wrapper select')

        projectDropdownWrapper.forEach(select => {
            select.style.width = '100%'
        })
    }

    // The project dropdowns will be reactive to selection changes.
    document.addEventListener('change', event => {
        if (event.target.matches(projectDropdownSelector)) {
            updateProjectDropdowns()
        }
    })

    // Initial update of project dropdowns
    updateProjectDropdowns()

    // Initially remove not necessary add buttons
    removeAddAndChangeButtons()
})