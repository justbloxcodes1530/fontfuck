(function() {
    // 1. Inject the @font-face rule so the browser knows where to find your installed font
    const style = document.createElement('style');
    style.textContent = `
        @font-face {
            font-family: 'Fuck Script';
            src: local('Fuck Script'), local('FuckScript');
        }
        * {
            font-family: 'Fuck Script', sans-serif !important;
        }
    `;
    document.head.appendChild(style);

    // 2. Force override any elements that use inline styles to block standard fonts
    const allElements = document.querySelectorAll('*');
    for (let i = 0; i < allElements.length; i++) {
        allElements[i].style.setProperty('font-family', 'Fuck Script', 'important');
    }

    console.log("Webpage Fuck Script'd successfully. Enjoy!");
})();
