// Automatically remove flash messages after 3 seconds
setTimeout(() => {
    const flashes = document.querySelector('.flashes');
    if (flashes) {
        flashes.remove();
    }
}, 3000);