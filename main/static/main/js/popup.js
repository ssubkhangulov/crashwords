// Get the modal
var popup_modal = document.querySelector(".popup")
// Get the button that opens the modal
var popup_btn = document.querySelector(".popup-button")
// Get the <span> element that closes the modal
var popup_close = document.querySelector(".popup-close")
// Set popup redirect after closing
var popup_redirect = null

// When the user clicks the button, open the modal
if (popup_btn !== null) {
  popup_btn.onclick = function() {
    popup_modal.style.display = "block"
  }
}

// When the user clicks on <span> (x), close the modal
popup_close.onclick = function() {
  popup_modal.style.display = "none"
  if (popup_redirect != null) {
    window.location.href = popup_redirect
  }
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == popup_modal) {
    popup_modal.style.display = "none"
    if (popup_redirect != null) {
      window.location.href = popup_redirect
    }
  }
}
