/**
 * Toggle user icons ph/ph-fill class.
 *
 * Adds a custom class "ph-users-dynamic" in order to simulate "white" and "black" with the fill status.
 */
function applyDynamicPhFill(isDark) {
	for (let el of document.getElementsByClassName("ph-fill-if-dark")) {
		el.classList.add(isDark ? "ph-fill" : "ph")
		el.classList.remove(isDark ? "ph" : "ph-fill")
	}
	for (let el of document.getElementsByClassName("ph-fill-if-light")) {
		el.classList.add(!isDark ? "ph-fill" : "ph")
		el.classList.remove(!isDark ? "ph" : "ph-fill")
	}
}

function isDarkMode() {
	return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
}

applyDynamicPhFill(isDarkMode())
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", event => { applyDynamicPhFill(event.matches) })
window.addEventListener("htmx:afterSwap", event => { applyDynamicPhFill(isDarkMode()) })
