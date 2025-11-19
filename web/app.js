document.addEventListener("DOMContentLoaded", () => {
    highlightActiveNav();
    setupAuthorFilters();
});

function highlightActiveNav() {
    const currentPage = document.body.dataset.page;
    if (!currentPage) {
        return;
    }
    const activeLink = document.querySelector(`[data-nav="${currentPage}"]`);
    if (activeLink) {
        activeLink.classList.add("active");
    }
}

function setupAuthorFilters() {
    const authorButtons = document.querySelectorAll("[data-author]");
    if (!authorButtons.length) {
        return;
    }

    const authorHeading = document.querySelector("[data-author-name]");
    const authorBooks = document.querySelector("[data-author-books]");

    const sampleData = {
        "Sabahattin Ali": [
            "Kürk Mantolu Madonna",
            "İçimizdeki Şeytan",
            "Kuyucaklı Yusuf"
        ],
        "Elif Şafak": [
            "Aşk",
            "10 Dakika 38 Saniye",
            "Baba ve Piç"
        ],
        "Orhan Pamuk": [
            "Kırmızı Saçlı Kadın",
            "Masumiyet Müzesi",
            "Kar"
        ]
    };

    authorButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const author = button.dataset.author;
            const books = sampleData[author] || [];

            authorHeading.textContent = author;
            if (books.length) {
                authorBooks.innerHTML = books
                    .map((title) => `<li>${title}</li>`)
                    .join("\n");
            } else {
                authorBooks.innerHTML = `<li>Bu yazar için kitap bulunamadı.</li>`;
            }
        });
    });
}
