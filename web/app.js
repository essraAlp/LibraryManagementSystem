// API Base URL - adjust this to your Django server URL
const API_BASE_URL = 'http://localhost:8000/api';

document.addEventListener("DOMContentLoaded", () => {
    highlightActiveNav();
    setupAuthorFilters();
    checkUserSession();
    
    // Initialize page-specific functionality
    const currentPage = document.body.dataset.page;
    if (currentPage === 'books') {
        initBookSearch();
        loadAllBooks();
    } else if (currentPage === 'profile') {
        initProfile();
    }
});

// ===== Authentication Functions =====

async function checkUserSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/session/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.logged_in) {
            updateUIForLoggedInUser(data);
        } else {
            updateUIForLoggedOutUser();
        }
    } catch (error) {
        console.error('Session check failed:', error);
        updateUIForLoggedOutUser();
    }
}

function updateUIForLoggedInUser(userData) {
    const greeting = document.getElementById('userGreeting');
    const loginBtn = document.getElementById('loginButton');
    const logoutBtn = document.getElementById('logoutButton');
    
    if (greeting) greeting.textContent = `Merhaba, ${userData.name}`;
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
}

function updateUIForLoggedOutUser() {
    const greeting = document.getElementById('userGreeting');
    const loginBtn = document.getElementById('loginButton');
    const logoutBtn = document.getElementById('logoutButton');
    
    if (greeting) greeting.textContent = 'Merhaba, Ziyaretçi';
    if (loginBtn) loginBtn.style.display = 'inline-block';
    if (logoutBtn) logoutBtn.style.display = 'none';
}

function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('loginError').style.display = 'none';
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            closeLoginModal();
            updateUIForLoggedInUser(data);
            // Reload page if on profile page
            if (document.body.dataset.page === 'profile') {
                location.reload();
            }
        } else {
            errorDiv.textContent = data.error || 'Giriş başarısız';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Bağlantı hatası';
        errorDiv.style.display = 'block';
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout/`, {
            method: 'POST',
            credentials: 'include'
        });
        
        updateUIForLoggedOutUser();
        
        // Redirect to books page if on profile page
        if (document.body.dataset.page === 'profile') {
            window.location.href = 'index.html';
        }
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// ===== Book Search Functions =====

function initBookSearch() {
    const searchButton = document.getElementById('searchButton');
    const clearButton = document.getElementById('clearSearch');
    const searchInput = document.getElementById('searchInput');
    
    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            clearButton.style.display = 'none';
            loadAllBooks();
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    console.log('[SEARCH] Starting search with query:', query);
    
    if (!query) {
        console.log('[SEARCH] Empty query, loading all books');
        loadAllBooks();
        return;
    }
    
    const searchInfo = document.getElementById('searchInfo');
    const clearButton = document.getElementById('clearSearch');
    const booksGrid = document.getElementById('booksGrid');
    
    // Show loading message
    booksGrid.innerHTML = '<p>Aranıyor...</p>';
    console.log('[SEARCH] Showing loading message');
    
    try {
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.log('[SEARCH] Request timeout after 30 seconds');
            controller.abort();
        }, 30000); // 30 second timeout
        
        const searchUrl = `${API_BASE_URL}/books/search/?q=${encodeURIComponent(query)}`;
        console.log('[SEARCH] Fetching URL:', searchUrl);
        console.log('[SEARCH] Fetch started at:', new Date().toISOString());
        
        const response = await fetch(searchUrl, {
            credentials: 'include',
            signal: controller.signal
        });
        
        console.log('[SEARCH] Response received at:', new Date().toISOString());
        console.log('[SEARCH] Response status:', response.status);
        console.log('[SEARCH] Response ok:', response.ok);
        console.log('[SEARCH] Response headers:', Object.fromEntries(response.headers.entries()));
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        console.log('[SEARCH] Starting to parse JSON...');
        const parseStartTime = Date.now();
        const data = await response.json();
        const parseEndTime = Date.now();
        console.log('[SEARCH] JSON parsed in', parseEndTime - parseStartTime, 'ms');
        console.log('[SEARCH] Data received:', {
            count: data.count,
            total: data.total,
            offset: data.offset,
            has_more: data.has_more,
            resultsLength: data.results ? data.results.length : 0
        });
        
        console.log('[SEARCH] Calling displayBooks with', data.results.length, 'books');
        displayBooks(data.results);
        
        searchInfo.textContent = `"${query}" için ${data.count} sonuç bulundu.`;
        clearButton.style.display = 'inline-block';
        console.log('[SEARCH] Search completed successfully');
        
    } catch (error) {
        console.error('[SEARCH] Error caught:', error);
        console.error('[SEARCH] Error name:', error.name);
        console.error('[SEARCH] Error message:', error.message);
        console.error('[SEARCH] Error stack:', error.stack);
        
        if (error.name === 'AbortError') {
            console.log('[SEARCH] Request was aborted due to timeout');
            searchInfo.textContent = 'Arama zaman aşımına uğradı. Lütfen daha spesifik bir arama yapın.';
            booksGrid.innerHTML = '<p>Arama çok uzun sürdü. Lütfen tekrar deneyin.</p>';
        } else {
            console.log('[SEARCH] Request failed with error');
            searchInfo.textContent = `Arama hatası: ${error.message}`;
            booksGrid.innerHTML = '<p>Arama sırasında bir hata oluştu. Konsolu kontrol edin.</p>';
        }
    }
}

async function loadAllBooks() {
    const searchInfo = document.getElementById('searchInfo');
    const booksGrid = document.getElementById('booksGrid');
    
    booksGrid.innerHTML = '<p>Kitaplar yükleniyor...</p>';
    
    try {
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        // Load only first 50 books for better performance
        const response = await fetch(`${API_BASE_URL}/books/?limit=50`, {
            credentials: 'include',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        displayBooks(data.results);
        const totalInfo = data.total ? ` (Toplam ${data.total} kitaptan ${data.count} tanesi gösteriliyor)` : '';
        searchInfo.textContent = `Kitaplar gösteriliyor${totalInfo}.`;
        
    } catch (error) {
        console.error('Failed to load books:', error);
        if (error.name === 'AbortError') {
            booksGrid.innerHTML = '<p>Yükleme zaman aşımına uğradı. Lütfen sayfayı yenileyin.</p>';
        } else {
            booksGrid.innerHTML = `<p>Kitaplar yüklenirken bir hata oluştu: ${error.message}</p>`;
        }
    }
}

function displayBooks(books) {
    console.log('[DISPLAY] displayBooks called with', books.length, 'books');
    const booksGrid = document.getElementById('booksGrid');
    
    if (!booksGrid) {
        console.error('[DISPLAY] ERROR: booksGrid element not found!');
        return;
    }
    
    if (!books || books.length === 0) {
        console.log('[DISPLAY] No books to display');
        booksGrid.innerHTML = '<p>Kitap bulunamadı.</p>';
        return;
    }
    
    console.log('[DISPLAY] Sample book data:', books[0]);
    console.log('[DISPLAY] Generating HTML for books...');
    
    try {
        booksGrid.innerHTML = books.map(book => {
        const availabilityBadge = book.available 
            ? '<span class="availability-badge available">Mevcut</span>'
            : '<span class="availability-badge unavailable">Ödünç Verilmiş</span>';
        
        const returnDate = !book.available && book.expected_return_date
            ? `<p class="expected-return">Beklenen iade tarihi: ${formatDate(book.expected_return_date)}</p>`
            : '';
        
        return `
            <article class="book-card">
                <h3>${escapeHtml(book.name)}</h3>
                <p><strong>Yazar:</strong> ${escapeHtml(book.author)}</p>
                <p><strong>Yayınevi:</strong> ${escapeHtml(book.publisher)}</p>
                <p><strong>Tür:</strong> ${escapeHtml(book.type)}</p>
                ${book.year ? `<p><strong>Yıl:</strong> ${book.year}</p>` : ''}
                <p>${escapeHtml(book.explanation)}</p>
                ${availabilityBadge}
                ${returnDate}
            </article>
        `;
        }).join('');
        console.log('[DISPLAY] HTML generated and inserted into DOM');
        console.log('[DISPLAY] Final booksGrid innerHTML length:', booksGrid.innerHTML.length);
    } catch (error) {
        console.error('[DISPLAY] Error generating HTML:', error);
        booksGrid.innerHTML = '<p>Kitaplar görüntülenirken bir hata oluştu.</p>';
    }
}

// ===== Profile Functions =====

async function initProfile() {
    try {
        const sessionResponse = await fetch(`${API_BASE_URL}/auth/session/`, {
            credentials: 'include'
        });
        const sessionData = await sessionResponse.json();
        
        if (!sessionData.logged_in || sessionData.type !== 'student') {
            document.getElementById('loginRequired').style.display = 'block';
            document.getElementById('profileContent').style.display = 'none';
            return;
        }
        
        document.getElementById('loginRequired').style.display = 'none';
        document.getElementById('profileContent').style.display = 'block';
        
        await loadBorrowings();
        await loadProfileInfo();
        
        // Setup profile form submission
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', handleProfileUpdate);
        }
    } catch (error) {
        console.error('Profile initialization failed:', error);
    }
}

async function loadBorrowings() {
    const borrowingsList = document.getElementById('borrowingsList');
    
    try {
        const response = await fetch(`${API_BASE_URL}/member/borrowings/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok) {
            displayBorrowings(data.borrowings);
        } else {
            borrowingsList.innerHTML = '<p>Ödünç alma kayıtları yüklenemedi.</p>';
        }
    } catch (error) {
        console.error('Failed to load borrowings:', error);
        borrowingsList.innerHTML = '<p>Ödünç alma kayıtları yüklenirken bir hata oluştu.</p>';
    }
}

function displayBorrowings(borrowings) {
    const borrowingsList = document.getElementById('borrowingsList');
    
    if (borrowings.length === 0) {
        borrowingsList.innerHTML = '<p>Henüz ödünç alma kaydınız bulunmamaktadır.</p>';
        return;
    }
    
    borrowingsList.innerHTML = borrowings.map(borrow => {
        const statusClass = borrow.status.toLowerCase();
        const statusText = {
            'active': 'Aktif',
            'late': 'Geç',
            'returned': 'İade Edildi'
        }[borrow.status] || borrow.status;
        
        let fineHtml = '';
        if (borrow.fine) {
            const fineClass = borrow.fine.status === 'paid' ? 'paid' : '';
            const fineStatus = borrow.fine.status === 'paid' ? 'Ödendi' : 'Ödenmedi';
            fineHtml = `
                <div class="fine-info ${fineClass}">
                    <strong>Ceza:</strong> ${borrow.fine.amount} TL - ${fineStatus}<br>
                    <strong>Ceza Tarihi:</strong> ${formatDate(borrow.fine.date)}
                    ${borrow.fine.payment_date ? `<br><strong>Ödeme Tarihi:</strong> ${formatDate(borrow.fine.payment_date)}` : ''}
                </div>
            `;
        }
        
        return `
            <div class="borrowing-card ${statusClass}">
                <div class="borrowing-header">
                    <h3>${escapeHtml(borrow.book.name)}</h3>
                    <span class="borrowing-status ${statusClass}">${statusText}</span>
                </div>
                <div class="borrowing-details">
                    <strong>Yazar:</strong> ${escapeHtml(borrow.book.author)}<br>
                    <strong>Ödünç Alma Tarihi:</strong> ${formatDate(borrow.borrow_date)}<br>
                    <strong>Son İade Tarihi:</strong> ${formatDate(borrow.last_return_date)}
                </div>
                ${fineHtml}
            </div>
        `;
    }).join('');
}

async function loadProfileInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/member/profile/`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('userName').value = data.name;
            document.getElementById('username').value = data.username;
            document.getElementById('userEmail').value = data.email;
            document.getElementById('userPhone').value = data.phone;
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
    }
}

async function handleProfileUpdate(event) {
    event.preventDefault();
    
    const email = document.getElementById('userEmail').value;
    const phone = document.getElementById('userPhone').value;
    const password = document.getElementById('userPassword').value;
    const messageDiv = document.getElementById('updateMessage');
    
    const updateData = { email, phone };
    if (password) {
        updateData.password = password;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/member/profile/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            messageDiv.className = 'message-success';
            messageDiv.textContent = 'Bilgileriniz başarıyla güncellendi!';
            messageDiv.style.display = 'block';
            document.getElementById('userPassword').value = '';
        } else {
            messageDiv.className = 'message-error';
            messageDiv.textContent = data.error || 'Güncelleme başarısız';
            messageDiv.style.display = 'block';
        }
    } catch (error) {
        messageDiv.className = 'message-error';
        messageDiv.textContent = 'Bağlantı hatası';
        messageDiv.style.display = 'block';
    }
}

// ===== Utility Functions =====

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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
