document.getElementById('menu__toggle').addEventListener('change', function () {
    if (this.checked) {
        document.body.classList.add('no-scroll');
    } else {
        document.body.classList.remove('no-scroll');
    }
});

document.querySelectorAll('.burger-menu__nav_nav').forEach(link => {
    link.addEventListener('click', () => {
        document.getElementById('menu__toggle').checked = false;
        document.body.classList.remove('no-scroll');
    });
});
