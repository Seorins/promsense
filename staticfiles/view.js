
document.addEventListener("DOMContentLoaded", function () {
    const popupShown = sessionStorage.getItem("popup_shown");

    const isAuthenticated = "{{ user.is_authenticated|yesno:'true,false' }}";

    if (isAuthenticated === 'false') {
        if (!popupShown) {
            const modal = new bootstrap.Modal(document.getElementById('welcomeModal'));
            modal.show(); 
            sessionStorage.setItem("popup_shown", "true");  
        }
    }
});

