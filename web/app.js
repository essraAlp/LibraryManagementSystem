// API Base URL - adjust this to your Django server URL
const API_BASE_URL = 'http://localhost:8000/api';

// Global state for pagination
let currentSearchQuery = null;
let currentOffset = 0;
let hasMoreResults = false;
let totalResults = 0;
let isLoadingMore = false;

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
            showMainContent();
        } else {
            updateUIForLoggedOutUser();
            hideMainContentAndShowLogin();
        }
    } catch (error) {
        console.error('Session check failed:', error);
        updateUIForLoggedOutUser();
        hideMainContentAndShowLogin();
    }
}

function showMainContent() {
    const main = document.querySelector('main');
    if (main) main.style.display = 'block';
}

function hideMainContentAndShowLogin() {
    const main = document.querySelector('main');
    if (main) main.style.display = 'none';
    showLoginModal();
}

function updateUIForLoggedInUser(userData) {
    const greeting = document.getElementById('userGreeting');
    const loginBtn = document.getElementById('loginButton');
    const logoutBtn = document.getElementById('logoutButton');
    
    if (greeting) greeting.textContent = `Merhaba, ${userData.name}`;
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
    
    // Add staff panel link if user is staff
    const nav = document.querySelector('nav');
    if (userData.type === 'staff' && nav && !document.querySelector('[data-nav="staff"]')) {
        const staffLink = document.createElement('a');
        staffLink.href = 'staff_panel.html';
        staffLink.setAttribute('data-nav', 'staff');
        staffLink.textContent = 'Personel Paneli';
        nav.appendChild(staffLink);
        highlightActiveNav();
    }
}

function updateUIForLoggedOutUser() {
    const greeting = document.getElementById('userGreeting');
    const loginBtn = document.getElementById('loginButton');
    const logoutBtn = document.getElementById('logoutButton');
    
    if (greeting) greeting.textContent = 'Merhaba, Ziyaretçi';
    if (loginBtn) loginBtn.style.display = 'inline-block';
    if (logoutBtn) logoutBtn.style.display = 'none';
    
    // Remove staff panel link if exists
    const staffLink = document.querySelector('[data-nav="staff"]');
    if (staffLink) {
        staffLink.remove();
    }
}

function showLoginModal() {
    const modal = document.getElementById('loginModal');
    const closeBtn = document.getElementById('closeLoginBtn');
    modal.style.display = 'flex';
    
    // Show close button only if user is already logged out and manually opening
    // Don't show it on initial page load when forcing login
    if (closeBtn) {
        closeBtn.style.display = 'none';
    }
}

function showLoginModalWithClose() {
    const modal = document.getElementById('loginModal');
    const closeBtn = document.getElementById('closeLoginBtn');
    modal.style.display = 'flex';
    
    if (closeBtn) {
        closeBtn.style.display = 'block';
    }
}

function closeLoginModal() {
    const modal = document.getElementById('loginModal');
    const errorDiv = document.getElementById('loginError');
    modal.style.display = 'none';
    if (errorDiv) errorDiv.style.display = 'none';
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
        
        console.log('Login response:', data); // Debug log
        
        if (response.ok && data.success) {
            closeLoginModal();
            
            // Redirect staff to staff panel immediately
            if (data.type === 'staff') {
                console.log('Redirecting to staff panel...'); // Debug log
                window.location.href = 'staff_panel.html';
                return;
            }
            
            // For students, update UI and show content
            updateUIForLoggedInUser(data);
            showMainContent();
            
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
        
        // Redirect to books page and show login modal
        if (document.body.dataset.page === 'profile' || document.body.dataset.page === 'staff') {
            window.location.href = 'index.html';
        } else {
            // Hide content and show login modal after logout
            hideMainContentAndShowLogin();
        }
    } catch (error) {
        console.error('Logout error:', error);
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
        currentSearchQuery = null;
        currentOffset = 0;
        loadAllBooks();
        return;
    }
    
    // Reset pagination for new search
    currentSearchQuery = query;
    currentOffset = 0;
    
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
        
        const searchUrl = `${API_BASE_URL}/books/search/?q=${encodeURIComponent(query)}&limit=50&offset=${currentOffset}`;
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
        
        // Update global state
        totalResults = data.total;
        hasMoreResults = data.has_more;
        
        console.log('[SEARCH] Calling displayBooks with', data.results.length, 'books');
        displayBooks(data.results, false);
        
        searchInfo.textContent = `"${query}" için ${data.total} sonuç bulundu.`;
        clearButton.style.display = 'inline-block';
        
        // Show or hide load more button
        updateLoadMoreButton();
        
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
    
    // Reset pagination
    currentSearchQuery = null;
    currentOffset = 0;
    
    booksGrid.innerHTML = '<p>Kitaplar yükleniyor...</p>';
    
    try {
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        // Load only first 50 books for better performance
        const response = await fetch(`${API_BASE_URL}/books/?limit=50&offset=${currentOffset}`, {
            credentials: 'include',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update global state
        totalResults = data.total || data.count;
        hasMoreResults = data.has_more || false;
        
        displayBooks(data.results, false);
        const totalInfo = data.total ? ` (Toplam ${data.total} kitap)` : '';
        searchInfo.textContent = `Kitaplar gösteriliyor${totalInfo}.`;
        
        // Show or hide load more button
        updateLoadMoreButton();
        
    } catch (error) {
        console.error('Failed to load books:', error);
        if (error.name === 'AbortError') {
            booksGrid.innerHTML = '<p>Yükleme zaman aşımına uğradı. Lütfen sayfayı yenileyin.</p>';
        } else {
            booksGrid.innerHTML = `<p>Kitaplar yüklenirken bir hata oluştu: ${error.message}</p>`;
        }
    }
}

function displayBooks(books, append = false) {
    console.log('[DISPLAY] displayBooks called with', books.length, 'books, append:', append);
    const booksGrid = document.getElementById('booksGrid');
    
    if (!booksGrid) {
        console.error('[DISPLAY] ERROR: booksGrid element not found!');
        return;
    }
    
    if (!books || books.length === 0) {
        if (!append) {
            console.log('[DISPLAY] No books to display');
            booksGrid.innerHTML = '<p>Kitap bulunamadı.</p>';
        }
        return;
    }
    
    console.log('[DISPLAY] Sample book data:', books[0]);
    console.log('[DISPLAY] Generating HTML for books...');
    
    try {
        const booksHTML = books.map(book => {
        const availabilityBadge = book.available 
            ? '<span class="availability-badge available">Mevcut</span>'
            : '<span class="availability-badge unavailable">Ödünç Verilmiş</span>';
        
        const returnDate = !book.available && book.expected_return_date
            ? `<p class="expected-return">Beklenen iade tarihi: ${formatDate(book.expected_return_date)}</p>`
            : '';
        
        // Truncate explanation to first 50 characters
        const explanation = book.explanation || '';
        const truncatedExplanation = explanation.length > 50 
            ? explanation.substring(0, 50) + '...' 
            : explanation;
        const showMoreButton = explanation.length > 50 
            ? `<button class="show-more-btn" onclick="showBookDetail('${book.isbn}')">Devamını Oku</button>` 
            : '';
        
        return `
            <article class="book-card" data-isbn="${book.isbn}">
                <h3>${escapeHtml(book.name)}</h3>
                <p><strong>Yazar:</strong> ${escapeHtml(book.author)}</p>
                <p><strong>Yayınevi:</strong> ${escapeHtml(book.publisher)}</p>
                <p><strong>Tür:</strong> ${escapeHtml(book.type)}</p>
                ${book.year ? `<p><strong>Yıl:</strong> ${book.year}</p>` : ''}
                <p class="book-explanation">${escapeHtml(truncatedExplanation)}</p>
                ${showMoreButton}
                ${availabilityBadge}
                ${returnDate}
            </article>
        `;
        }).join('');
        
        if (append) {
            booksGrid.innerHTML += booksHTML;
        } else {
            booksGrid.innerHTML = booksHTML;
        }
        
        console.log('[DISPLAY] HTML generated and inserted into DOM');
        console.log('[DISPLAY] Final booksGrid innerHTML length:', booksGrid.innerHTML.length);
    } catch (error) {
        console.error('[DISPLAY] Error generating HTML:', error);
        if (!append) {
            booksGrid.innerHTML = '<p>Kitaplar görüntülenirken bir hata oluştu.</p>';
        }
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
    const messageDiv = document.getElementById('updateMessage');
    
    const updateData = { email, phone };
    
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
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 3000);
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

// Password Change Modal Functions
function showPasswordModal() {
    document.getElementById('passwordModal').style.display = 'flex';
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
    document.getElementById('passwordError').style.display = 'none';
    document.getElementById('passwordSuccess').style.display = 'none';
}

function closePasswordModal() {
    document.getElementById('passwordModal').style.display = 'none';
}

async function handlePasswordChange(event) {
    event.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorDiv = document.getElementById('passwordError');
    const successDiv = document.getElementById('passwordSuccess');
    
    // Hide previous messages
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    // Validate new password confirmation
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'Yeni şifreler eşleşmiyor!';
        errorDiv.style.display = 'block';
        return;
    }
    
    // Validate password length
    if (newPassword.length < 4) {
        errorDiv.textContent = 'Şifre en az 4 karakter olmalıdır!';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/member/profile/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                password: newPassword,
                current_password: currentPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            successDiv.textContent = 'Şifreniz başarıyla değiştirildi!';
            successDiv.style.display = 'block';
            
            // Close modal after 2 seconds
            setTimeout(() => {
                closePasswordModal();
            }, 2000);
        } else {
            errorDiv.textContent = data.error || 'Şifre değiştirme başarısız';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Bağlantı hatası: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// ===== Utility Functions =====

async function showBookDetail(isbn) {
    const modal = document.getElementById('bookDetailModal');
    const modalContent = document.getElementById('bookDetailContent');
    
    // Show modal with loading message
    modal.style.display = 'flex';
    modalContent.innerHTML = '<p>Yükleniyor...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/books/${encodeURIComponent(isbn)}/`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const book = await response.json();
        
        // Display full book details in modal
        const availabilityBadge = book.available 
            ? '<span class="availability-badge available">Mevcut</span>'
            : '<span class="availability-badge unavailable">Ödünç Verilmiş</span>';
        
        const returnDate = !book.available && book.expected_return_date
            ? `<p class="expected-return"><strong>Beklenen iade tarihi:</strong> ${formatDate(book.expected_return_date)}</p>`
            : '';
        
        const bookImage = book.image 
            ? `<img src="${escapeHtml(book.image)}" alt="${escapeHtml(book.name)}" class="book-detail-image" onerror="this.style.display='none'">` 
            : '';
        
        modalContent.innerHTML = `
            <div class="book-detail-container">
                ${bookImage}
                <div class="book-detail-info">
                    <h2>${escapeHtml(book.name)}</h2>
                    <p><strong>Yazar:</strong> ${escapeHtml(book.author)}</p>
                    <p><strong>Yayınevi:</strong> ${escapeHtml(book.publisher)}</p>
                    <p><strong>Tür:</strong> ${escapeHtml(book.type)}</p>
                    ${book.year ? `<p><strong>Yıl:</strong> ${book.year}</p>` : ''}
                    <p><strong>ISBN:</strong> ${escapeHtml(book.isbn)}</p>
                    ${availabilityBadge}
                    ${returnDate}
                    <div class="book-full-explanation">
                        <h3>Açıklama</h3>
                        <p>${escapeHtml(book.explanation)}</p>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to load book details:', error);
        modalContent.innerHTML = '<p>Kitap detayları yüklenirken bir hata oluştu.</p>';
    }
}

function closeBookDetailModal() {
    const modal = document.getElementById('bookDetailModal');
    modal.style.display = 'none';
}

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

// ===== Pagination Functions =====

function updateLoadMoreButton() {
    let loadMoreContainer = document.getElementById('loadMoreContainer');
    
    // Create container if it doesn't exist
    if (!loadMoreContainer) {
        loadMoreContainer = document.createElement('div');
        loadMoreContainer.id = 'loadMoreContainer';
        loadMoreContainer.style.textAlign = 'center';
        loadMoreContainer.style.marginTop = '2rem';
        loadMoreContainer.style.marginBottom = '2rem';
        
        const booksGrid = document.getElementById('booksGrid');
        if (booksGrid && booksGrid.parentNode) {
            booksGrid.parentNode.insertBefore(loadMoreContainer, booksGrid.nextSibling);
        }
    }
    
    if (hasMoreResults && !isLoadingMore) {
        const currentlyShown = currentOffset + 50;
        loadMoreContainer.innerHTML = `
            <p style="color: #52606d; margin-bottom: 1rem;">
                ${currentlyShown} / ${totalResults} kitap gösteriliyor
            </p>
            <button onclick="loadMoreBooks()" style="
                background-color: #1d3557;
                color: #f1faee;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 2rem;
                font-size: 1rem;
                cursor: pointer;
                transition: background-color 0.2s;
            " onmouseover="this.style.backgroundColor='#2d4567'" 
               onmouseout="this.style.backgroundColor='#1d3557'">
                Daha Fazla Yükle
            </button>
        `;
    } else if (isLoadingMore) {
        loadMoreContainer.innerHTML = `
            <p style="color: #52606d;">Yükleniyor...</p>
        `;
    } else {
        loadMoreContainer.innerHTML = '';
    }
}

async function loadMoreBooks() {
    if (isLoadingMore || !hasMoreResults) {
        return;
    }
    
    isLoadingMore = true;
    updateLoadMoreButton();
    
    try {
        currentOffset += 50;
        
        let url;
        if (currentSearchQuery) {
            // Loading more search results
            url = `${API_BASE_URL}/books/search/?q=${encodeURIComponent(currentSearchQuery)}&limit=50&offset=${currentOffset}`;
        } else {
            // Loading more all books
            url = `${API_BASE_URL}/books/?limit=50&offset=${currentOffset}`;
        }
        
        const response = await fetch(url, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update global state
        hasMoreResults = data.has_more || false;
        totalResults = data.total || totalResults;
        
        // Append new books to existing ones
        displayBooks(data.results, true);
        
        isLoadingMore = false;
        updateLoadMoreButton();
        
    } catch (error) {
        console.error('Failed to load more books:', error);
        isLoadingMore = false;
        updateLoadMoreButton();
        alert('Daha fazla kitap yüklenirken bir hata oluştu.');
    }
}
