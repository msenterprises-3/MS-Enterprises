// Main Interactive Client-Side Logic for MS Enterprises

// Testimonials Public Submission Form helpers (Declared early for immediate availability)
window.openTestimonialForm = function() {
    const container = document.getElementById('testimonialFormContainer');
    if (container) {
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth' });
    }
};
window.openReviewForm = window.openTestimonialForm;
window.toggleReviewModal = window.openTestimonialForm;

window.closeTestimonialForm = function() {
    const container = document.getElementById('testimonialFormContainer');
    if (container) {
        container.style.display = 'none';
        const form = document.getElementById('testimonialSubmitForm');
        if (form) form.reset();
        const statusDiv = document.getElementById('tFormStatus');
        if (statusDiv) statusDiv.style.display = 'none';
    }
};

window.submitTestimonialReview = function(event) {
    if (event) event.preventDefault();
    const nameEl = document.getElementById('tFormName');
    const cityEl = document.getElementById('tFormCity');
    const ratingEl = document.getElementById('tFormRating');
    const reviewEl = document.getElementById('tFormReviewText');
    const statusDiv = document.getElementById('tFormStatus');
    
    const name = nameEl ? nameEl.value.trim() : '';
    const city = cityEl ? cityEl.value.trim() : '';
    const rating = ratingEl ? parseInt(ratingEl.value) : 5;
    const review = reviewEl ? reviewEl.value.trim() : '';
    
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.color = 'var(--primary-color)';
        statusDiv.innerText = 'Submitting your review...';
    }
    
    fetch('/api/testimonials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            customer_name: name,
            city: city,
            rating: rating,
            review: review
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (statusDiv) {
                statusDiv.style.color = '#27AE60';
                statusDiv.innerText = data.message || 'Thank you! Your review has been submitted for approval.';
            }
            if (typeof showCartToast === 'function') {
                showCartToast("Thank you! Review submitted for approval.");
            }
            setTimeout(() => {
                window.closeTestimonialForm();
            }, 3000);
        } else {
            if (statusDiv) {
                statusDiv.style.color = '#E74C3C';
                statusDiv.innerText = data.message || 'Error submitting review.';
            }
        }
    })
    .catch(err => {
        console.error("Testimonial submit error:", err);
        if (statusDiv) {
            statusDiv.style.color = '#E74C3C';
            statusDiv.innerText = 'Failed to submit review due to server error.';
        }
    });
};

function initMainApp() {
    if (window.__mainAppInitialized) {
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch (e) {}
        }
        return;
    }
    window.__mainAppInitialized = true;

    // 1. Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        try {
            lucide.createIcons();
        } catch (e) {}
    }

    // 2. Mobile Hamburger Menu & Search Toggle
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');
    const searchMobileToggle = document.getElementById('searchMobileToggle');
    const searchContainer = document.querySelector('.search-container');

    if (hamburgerBtn && mobileDropdownMenu) {
        hamburgerBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = mobileDropdownMenu.classList.toggle('active');
            hamburgerBtn.classList.toggle('active', isOpen);
            // Close search if open
            if (searchContainer && searchContainer.classList.contains('active')) {
                searchContainer.classList.remove('active');
            }
        });
    }

    if (searchMobileToggle && searchContainer) {
        searchMobileToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = searchContainer.classList.toggle('active');
            if (isOpen) {
                const input = searchContainer.querySelector('.search-input');
                if (input) input.focus();
                // Close hamburger menu if open
                if (mobileDropdownMenu && mobileDropdownMenu.classList.contains('active')) {
                    mobileDropdownMenu.classList.remove('active');
                    if (hamburgerBtn) hamburgerBtn.classList.remove('active');
                }
            }
        });
    }

    // Close mobile dropdown and search when clicking outside
    document.addEventListener('click', function (e) {
        if (mobileDropdownMenu && mobileDropdownMenu.classList.contains('active')) {
            if (!mobileDropdownMenu.contains(e.target) && !hamburgerBtn.contains(e.target)) {
                mobileDropdownMenu.classList.remove('active');
                if (hamburgerBtn) hamburgerBtn.classList.remove('active');
            }
        }
        if (searchContainer && searchContainer.classList.contains('active')) {
            if (!searchContainer.contains(e.target) && !searchMobileToggle.contains(e.target)) {
                searchContainer.classList.remove('active');
            }
        }
    });

    // Desktop and Mobile Click-to-Open Category Menu
    const categoriesMenuToggle = document.getElementById('categoriesMenuToggle');
    if (categoriesMenuToggle) {
        categoriesMenuToggle.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent document click from immediately closing it
            const dropdown = this.closest('.nav-link-dropdown');
            if (dropdown) {
                dropdown.classList.toggle('active');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            const dropdown = document.querySelector('.nav-link-dropdown.active');
            if (dropdown && !dropdown.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
    }

    // Mega Dropdown Category Menu Tab Switcher
    const tabItems = document.querySelectorAll('.mega-menu-tab-item');
    if (tabItems.length > 0) {
        tabItems.forEach(item => {
            const handleTabSwitch = function(e) {
                if (e.type === 'click') {
                    e.preventDefault();
                    e.stopPropagation();
                }
                
                // Remove active from all tabs in this menu
                const parentList = this.closest('.mega-menu-tabs');
                if (parentList) {
                    parentList.querySelectorAll('.mega-menu-tab-item').forEach(tab => tab.classList.remove('active'));
                }
                this.classList.add('active');

                // Hide all panels
                const container = this.closest('.mega-menu-tabs-container');
                if (container) {
                    const panelsContainer = container.querySelector('.mega-menu-panels');
                    if (panelsContainer) {
                        panelsContainer.querySelectorAll('.mega-menu-panel').forEach(panel => panel.classList.remove('active'));
                        
                        // Show target panel
                        const targetId = this.getAttribute('data-tab');
                        const targetPanel = panelsContainer.querySelector('#' + targetId);
                        if (targetPanel) {
                            targetPanel.classList.add('active');
                        }
                    }
                }
            };
            
            item.addEventListener('mouseenter', function(e) {
                if (window.innerWidth > 991) {
                    handleTabSwitch.call(this, e);
                }
            });
            
            item.addEventListener('click', handleTabSwitch);
        });
    }

    // 3. Hero Slider Carousel
    const heroSlider = document.getElementById('heroSlider');
    if (heroSlider) {
        const slides = Array.from(heroSlider.querySelectorAll('.slide'));
        const dots = Array.from(heroSlider.querySelectorAll('.dot'));
        const prevBtn = document.getElementById('sliderPrevBtn');
        const nextBtn = document.getElementById('sliderNextBtn');
        let currentSlide = 0;
        let slideInterval = null;

        function showSlide(index) {
            if (!slides || slides.length === 0) return;
            
            // Wrap index
            if (index >= slides.length) currentSlide = 0;
            else if (index < 0) currentSlide = slides.length - 1;
            else currentSlide = index;

            slides.forEach((s, idx) => {
                if (idx === currentSlide) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });

            dots.forEach((d, idx) => {
                if (idx === currentSlide) {
                    d.classList.add('active');
                } else {
                    d.classList.remove('active');
                }
            });
        }

        function startSlideShow() {
            stopSlideShow();
            slideInterval = setInterval(function () {
                showSlide(currentSlide + 1);
            }, 5000);
        }

        function stopSlideShow() {
            if (slideInterval) {
                clearInterval(slideInterval);
                slideInterval = null;
            }
        }

        function handlePrev(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            stopSlideShow();
            showSlide(currentSlide - 1);
            startSlideShow();
        }

        function handleNext(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            stopSlideShow();
            showSlide(currentSlide + 1);
            startSlideShow();
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', handlePrev);
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', handleNext);
        }

        dots.forEach((dot, idx) => {
            dot.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                stopSlideShow();
                showSlide(idx);
                startSlideShow();
            });
        });

        // Pause on hover
        heroSlider.addEventListener('mouseenter', stopSlideShow);
        heroSlider.addEventListener('mouseleave', startSlideShow);

        // Mobile touch swipe support
        let touchStartX = 0;
        let touchEndX = 0;
        heroSlider.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        heroSlider.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            if (touchEndX < touchStartX - 40) {
                handleNext();
            } else if (touchEndX > touchStartX + 40) {
                handlePrev();
            }
        }, { passive: true });

        // Start
        startSlideShow();
    }

    // 3b. Customer Spotlight Video Slider Carousel
    const videoSlider = document.getElementById('videoSlider');
    if (videoSlider) {
        const vSlides = Array.from(videoSlider.querySelectorAll('.video-slide'));
        const vDots = Array.from(videoSlider.querySelectorAll('.video-dot'));
        const vPrevBtn = document.getElementById('videoPrevBtn');
        const vNextBtn = document.getElementById('videoNextBtn');
        let currentVSlide = 0;
        let vSlideInterval = null;

        function showVSlide(index) {
            if (!vSlides || vSlides.length === 0) return;
            
            // Wrap index
            if (index >= vSlides.length) currentVSlide = 0;
            else if (index < 0) currentVSlide = vSlides.length - 1;
            else currentVSlide = index;

            vSlides.forEach((s, idx) => {
                if (idx === currentVSlide) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });

            vDots.forEach((d, idx) => {
                if (idx === currentVSlide) {
                    d.classList.add('active');
                } else {
                    d.classList.remove('active');
                }
            });
        }

        function startVSlideShow() {
            stopVSlideShow();
            vSlideInterval = setInterval(function () {
                showVSlide(currentVSlide + 1);
            }, 6000);
        }

        function stopVSlideShow() {
            if (vSlideInterval) {
                clearInterval(vSlideInterval);
                vSlideInterval = null;
            }
        }

        function handleVPrev(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            stopVSlideShow();
            showVSlide(currentVSlide - 1);
            startVSlideShow();
        }

        function handleVNext(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            stopVSlideShow();
            showVSlide(currentVSlide + 1);
            startVSlideShow();
        }

        if (vPrevBtn) {
            vPrevBtn.addEventListener('click', handleVPrev);
        }
        if (vNextBtn) {
            vNextBtn.addEventListener('click', handleVNext);
        }

        vDots.forEach((dot, idx) => {
            dot.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                stopVSlideShow();
                showVSlide(idx);
                startVSlideShow();
            });
        });

        // Pause on hover
        videoSlider.addEventListener('mouseenter', stopVSlideShow);
        videoSlider.addEventListener('mouseleave', startVSlideShow);

        // Mobile touch swipe support
        let vTouchStartX = 0;
        let vTouchEndX = 0;
        videoSlider.addEventListener('touchstart', function(e) {
            vTouchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        videoSlider.addEventListener('touchend', function(e) {
            vTouchEndX = e.changedTouches[0].screenX;
            if (vTouchEndX < vTouchStartX - 40) {
                handleVNext();
            } else if (vTouchEndX > vTouchStartX + 40) {
                handleVPrev();
            }
        }, { passive: true });

        // Video playback detection: if user clicks inside iframe, pause slideshow
        window.addEventListener('blur', function () {
            setTimeout(function () {
                const activeEl = document.activeElement;
                if (activeEl && activeEl.tagName === 'IFRAME' && activeEl.closest('#videoSlider')) {
                    stopVSlideShow();
                }
            }, 100);
        });

        window.addEventListener('focus', function () {
            startVSlideShow();
        });

        // Start
        startVSlideShow();
    }

    // 4. Trust/Features tabbed panels in Homepage
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetTab = btn.dataset.tab;
            const targetEl = document.getElementById(targetTab);
            if (targetEl) {
                targetEl.classList.add('active');
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        });
    });

    // 5. Testimonial Text Slider Loop
    const testimonialTrack = document.getElementById('testimonialTrack');
    if (testimonialTrack) {
        const slides = testimonialTrack.querySelectorAll('.testimonial-slide');
        const prevBtn = document.getElementById('testPrev');
        const nextBtn = document.getElementById('testNext');
        let currentIdx = 0;

        function updateTestimonialSlider() {
            testimonialTrack.style.transform = `translateX(-${currentIdx * 100}%)`;
        }

        if (prevBtn && nextBtn) {
            prevBtn.addEventListener('click', function () {
                currentIdx = (currentIdx === 0) ? slides.length - 1 : currentIdx - 1;
                updateTestimonialSlider();
            });
            nextBtn.addEventListener('click', function () {
                currentIdx = (currentIdx === slides.length - 1) ? 0 : currentIdx + 1;
                updateTestimonialSlider();
            });
        }
    }

    // 6. Countdown Timer
    const countdownEl = document.getElementById('countdownTimer');
    if (countdownEl) {
        const endTimeStr = countdownEl.dataset.endtime; // ISO Date YYYY-MM-DD HH:MM:SS
        const daysSpan = document.getElementById('days');
        const hoursSpan = document.getElementById('hours');
        const minutesSpan = document.getElementById('minutes');
        const secondsSpan = document.getElementById('seconds');

        function updateTimer() {
            const end = new Date(endTimeStr.replace(' ', 'T')).getTime();
            const now = new Date().getTime();
            const diff = end - now;

            if (diff <= 0) {
                countdownEl.style.display = 'none';
                clearInterval(timerInterval);
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            let hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            const isMobile = window.innerWidth <= 768;
            if (isMobile) {
                const daysBox = document.getElementById('daysBox');
                const daysColon = document.getElementById('daysColon');
                if (daysBox) daysBox.style.display = 'none';
                if (daysColon) daysColon.style.display = 'none';
                
                const totalHours = hours + (days * 24);
                if (hoursSpan) hoursSpan.innerText = String(totalHours).padStart(2, '0');
            } else {
                const daysBox = document.getElementById('daysBox');
                const daysColon = document.getElementById('daysColon');
                if (daysBox) daysBox.style.display = 'flex';
                if (daysColon) daysColon.style.display = 'none';
                
                if (daysSpan) daysSpan.innerText = String(days).padStart(2, '0');
                if (hoursSpan) hoursSpan.innerText = String(hours).padStart(2, '0');
            }

            if (minutesSpan) minutesSpan.innerText = String(minutes).padStart(2, '0');
            if (secondsSpan) secondsSpan.innerText = String(seconds).padStart(2, '0');
        }

        updateTimer();
        const timerInterval = setInterval(updateTimer, 1000);
    }

    // 7. Instant Search Autocomplete Dropdown
    const searchInput = document.getElementById('searchInput');
    const autocompleteBox = document.getElementById('searchAutocomplete');
    let debounceTimer;

    if (searchInput && autocompleteBox) {
        searchInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const query = searchInput.value.trim();

            if (query.length < 2) {
                autocompleteBox.style.display = 'none';
                return;
            }

            debounceTimer = setTimeout(function () {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        autocompleteBox.innerHTML = '';
                        if (data.length === 0) {
                            autocompleteBox.style.display = 'none';
                            return;
                        }

                        data.forEach(item => {
                            const div = document.createElement('a');
                            div.href = `/product/${item.slug}`;
                            div.className = 'autocomplete-item';
                            
                            const priceText = item.offer_price 
                                ? `₹${item.offer_price.toLocaleString('en-IN')} <span style="text-decoration:line-through; font-size:10px; color:gray;">₹${item.price.toLocaleString('en-IN')}</span>`
                                : `₹${item.price.toLocaleString('en-IN')}`;

                            div.innerHTML = `
                                <img src="${item.image_url}" class="autocomplete-img" alt="${item.name}" onerror="this.onerror=null;this.src='/static/uploads/products/prod_generic_1.webp';">
                                <div class="autocomplete-info">
                                    <div class="autocomplete-name">${item.name}</div>
                                    <div class="autocomplete-price">${priceText}</div>
                                </div>
                            `;
                            autocompleteBox.appendChild(div);
                        });
                        autocompleteBox.style.display = 'block';
                    })
                    .catch(err => console.error("Search autocomplete error:", err));
            }, 300);
        });

        // Hide when clicking outside
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !autocompleteBox.contains(e.target)) {
                autocompleteBox.style.display = 'none';
            }
        });
    }

    // 8. Product Details Image Zoom Lens
    const zoomContainer = document.getElementById('zoomContainer');
    const mainImg = document.getElementById('mainProductImg');
    const zoomLens = document.getElementById('zoomLens');

    if (zoomContainer && mainImg && zoomLens) {
        zoomContainer.addEventListener('mousemove', function (e) {
            zoomLens.style.display = 'block';
            
            const rect = mainImg.getBoundingClientRect();
            
            // Pointer position relative to image
            let x = e.clientX - rect.left;
            let y = e.clientY - rect.top;
            
            // Ensure lens doesn't go outside image boundaries
            const lensWidth = zoomLens.offsetWidth;
            const lensHeight = zoomLens.offsetHeight;
            
            let lensX = x - lensWidth / 2;
            let lensY = y - lensHeight / 2;
            
            if (lensX < 0) lensX = 0;
            if (lensX > rect.width - lensWidth) lensX = rect.width - lensWidth;
            if (lensY < 0) lensY = 0;
            if (lensY > rect.height - lensHeight) lensY = rect.height - lensHeight;
            
            zoomLens.style.left = lensX + 'px';
            zoomLens.style.top = lensY + 'px';
            
            // Zoom magnification factor (e.g. 2.5x)
            const scaleX = mainImg.naturalWidth / rect.width;
            const scaleY = mainImg.naturalHeight / rect.height;
            
            zoomLens.style.backgroundImage = `url('${mainImg.src}')`;
            zoomLens.style.backgroundSize = (mainImg.naturalWidth) + "px " + (mainImg.naturalHeight) + "px";
            zoomLens.style.backgroundPosition = `-${lensX * scaleX}px -${lensY * scaleY}px`;
        });
        
        zoomContainer.addEventListener('mouseleave', function () {
            zoomLens.style.display = 'none';
        });
    }

    // 9. Customer Review Form API submit
    const reviewForm = document.getElementById('reviewSubmitForm');
    const reviewStatus = document.getElementById('reviewStatus');
    const reviewSubmitBtn = document.getElementById('revSubmitBtn') || (reviewForm ? reviewForm.querySelector('button[type="submit"]') : null);
    
    if (reviewForm) {
        reviewForm.addEventListener('submit', function (e) {
            e.preventDefault();
            console.log("Button clicked! (Submit Review)");
            
            const product_id = document.getElementById('revProductId') ? document.getElementById('revProductId').value : '';
            const reviewer_name = document.getElementById('revName') ? document.getElementById('revName').value.trim() : '';
            const ratingRadio = document.querySelector('input[name="revRating"]:checked');
            const rating = ratingRadio ? parseInt(ratingRadio.value) : 5;
            const review_text = document.getElementById('revText') ? document.getElementById('revText').value.trim() : '';
            const currentStatus = document.getElementById('reviewStatus') || reviewStatus;
            
            if (!reviewer_name || !review_text) {
                if (currentStatus) {
                    currentStatus.style.display = 'block';
                    currentStatus.style.color = '#b91c1c';
                    currentStatus.style.backgroundColor = '#fef2f2';
                    currentStatus.style.border = '1px solid #fecaca';
                    currentStatus.style.padding = '10px 14px';
                    currentStatus.style.borderRadius = '6px';
                    currentStatus.innerText = 'Please provide both your name and review details.';
                }
                return;
            }
            
            if (reviewSubmitBtn) {
                reviewSubmitBtn.disabled = true;
                reviewSubmitBtn.innerText = 'Submitting...';
            }
            
            if (currentStatus) {
                currentStatus.style.display = 'block';
                currentStatus.style.color = '#b45309';
                currentStatus.style.backgroundColor = '#fffbeb';
                currentStatus.style.border = '1px solid #fde68a';
                currentStatus.style.padding = '10px 14px';
                currentStatus.style.borderRadius = '6px';
                currentStatus.innerText = 'Submitting your review...';
            }
            
            fetch('/api/reviews', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id, reviewer_name, rating, review_text })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (currentStatus) {
                        currentStatus.style.display = 'block';
                        currentStatus.style.color = '#065f46';
                        currentStatus.style.backgroundColor = '#d1fae5';
                        currentStatus.style.border = '1px solid #a7f3d0';
                        currentStatus.innerText = 'Thank you! Your review has been submitted and is pending admin approval.';
                    }
                    reviewForm.reset();
                    const defaultStar = document.getElementById('rate5');
                    if (defaultStar) defaultStar.checked = true;
                    showCartToast("Thank you! Review submitted for approval.");
                } else {
                    if (currentStatus) {
                        currentStatus.style.display = 'block';
                        currentStatus.style.color = '#b91c1c';
                        currentStatus.style.backgroundColor = '#fef2f2';
                        currentStatus.style.border = '1px solid #fecaca';
                        currentStatus.innerText = data.message || 'Failed to submit review.';
                    }
                }
            })
            .catch(err => {
                console.error("Review submission error:", err);
                if (currentStatus) {
                    currentStatus.style.display = 'block';
                    currentStatus.style.color = '#b91c1c';
                    currentStatus.style.backgroundColor = '#fef2f2';
                    currentStatus.style.border = '1px solid #fecaca';
                    currentStatus.innerText = 'Failed to submit review. Please try again.';
                }
            })
            .finally(() => {
                if (reviewSubmitBtn) {
                    reviewSubmitBtn.disabled = false;
                    reviewSubmitBtn.innerText = 'Submit Review';
                }
            });
        });
    }

    // 10. Scroll to Top Floating Button
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 400) {
                scrollTopBtn.style.display = 'flex';
            } else {
                scrollTopBtn.style.display = 'none';
            }
        });
        
        scrollTopBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // 11. Shopping Cart Client-side State Manager (DB-Backed)
    let cachedCart = {}; // format: { productId: quantity }
    let cachedWishlist = []; // format: [ productId1, productId2, ... ]

    // Wishlist feature removed - safe compatibility stubs
    function getWishlist() {
        return [];
    }

    function toggleWishlist(id) {
        return false;
    }

    function getCart() {
        return cachedCart;
    }

    function addToCart(id, qty = 1, variantId = null) {
        console.log("Button clicked! (Add to Cart: " + id + ")");
        if (!id) return;
        id = String(id);
        qty = parseInt(qty) || 1;
        cachedCart[id] = (cachedCart[id] || 0) + qty;
        
        // Optimistic badge update immediately
        const totalItems = Object.values(cachedCart).reduce((a, b) => a + b, 0);
        updateBadges(totalItems);

        // Save in database
        fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: id, quantity: qty, variant_id: variantId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const finalCount = typeof data.cart_count !== 'undefined' ? data.cart_count : Object.values(cachedCart).reduce((a, b) => a + b, 0);
                updateBadges(finalCount);
                showCartToast(data.message || "Product added to cart!");
                window.dispatchEvent(new CustomEvent('cartUpdated', { detail: { productId: id, quantity: qty, cartCount: finalCount } }));
            } else {
                showCartToast(data.message || "Failed to add to cart.");
            }
        })
        .catch(err => {
            console.error("Error adding to cart:", err);
            showCartToast("Error adding product to cart.");
        });

        // Report stats
        fetch('/api/stats/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        }).catch(e => console.error("Stats error:", e));
    }

    function removeFromCart(id) {
        if (!id) return;
        id = String(id);
        delete cachedCart[id];
        const totalItems = Object.values(cachedCart).reduce((a, b) => a + b, 0);
        updateBadges(totalItems);

        // Remove from database
        fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const finalCount = typeof data.cart_count !== 'undefined' ? data.cart_count : Object.values(cachedCart).reduce((a, b) => a + b, 0);
                updateBadges(finalCount);
                window.dispatchEvent(new CustomEvent('cartUpdated', { detail: { productId: id, cartCount: finalCount } }));
            }
        })
        .catch(err => console.error("Error removing from cart:", err));
    }

    function updateCartQty(id, qty) {
        if (!id) return;
        id = String(id);
        qty = parseInt(qty) || 0;
        if (qty <= 0) {
            delete cachedCart[id];
        } else {
            cachedCart[id] = qty;
        }
        const totalItems = Object.values(cachedCart).reduce((a, b) => a + b, 0);
        updateBadges(totalItems);

        // Update in database
        fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: id, quantity: qty })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const finalCount = typeof data.cart_count !== 'undefined' ? data.cart_count : Object.values(cachedCart).reduce((a, b) => a + b, 0);
                updateBadges(finalCount);
                window.dispatchEvent(new CustomEvent('cartUpdated', { detail: { productId: id, quantity: qty, cartCount: finalCount } }));
            }
        })
        .catch(err => console.error("Error updating cart quantity:", err));
    }

    function updateBadges(cartCountOverride) {
        let cartCount = 0;
        if (typeof cartCountOverride !== 'undefined' && cartCountOverride !== null) {
            cartCount = parseInt(cartCountOverride) || 0;
        } else {
            cartCount = Object.values(cachedCart).reduce((a, b) => (parseInt(a) || 0) + (parseInt(b) || 0), 0);
        }

        document.querySelectorAll('.wishlist-badge').forEach(badge => {
            badge.style.setProperty('display', 'none', 'important');
        });

        const badges = document.querySelectorAll('.cart-badge, .cart-header-link .badge-count, .icon-badge-wrapper .badge-count, [data-cart-badge]');
        badges.forEach(badge => {
            if (cartCount > 0) {
                badge.innerText = String(cartCount);
                badge.textContent = String(cartCount);
                badge.style.setProperty('display', 'inline-flex', 'important');
                
                // Visual Pulse Indicator
                badge.classList.remove('badge-pulse');
                void badge.offsetWidth; // Trigger reflow for re-animation
                badge.classList.add('badge-pulse');
            } else {
                badge.innerText = '0';
                badge.textContent = '0';
                badge.style.setProperty('display', 'none', 'important');
                badge.classList.remove('badge-pulse');
            }
        });
    }

    function updateWishlistHeartUI() {}

    function showCartToast(msg) {
        let toast = document.getElementById('cartToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'cartToast';
            toast.style.cssText = `
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #1e293b;
                color: #ffffff;
                padding: 12px 24px;
                border-radius: 8px;
                border: 1px solid #c5a028;
                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                z-index: 99999;
                font-family: inherit;
                font-size: 14px;
                font-weight: 600;
                display: none;
                text-align: center;
                pointer-events: none;
                transition: opacity 0.3s ease, transform 0.3s ease;
            `;
            document.body.appendChild(toast);
        }
        toast.innerText = msg;
        toast.style.display = 'block';
        toast.style.opacity = '1';
        
        if (window.__cartToastTimeout) clearTimeout(window.__cartToastTimeout);
        window.__cartToastTimeout = setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => { toast.style.display = 'none'; }, 300);
        }, 2500);
    }

    // Wishlist initialization no-op
    function initWishlistHearts() {}

    // Fetch initial cart state from database and trigger badge rendering
    function syncStatesWithDatabase() {
        fetch('/api/cart')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    cachedCart = {};
                    let totalCount = 0;
                    if (data.items && Array.isArray(data.items)) {
                        data.items.forEach(item => {
                            cachedCart[item.product_id] = item.quantity;
                            totalCount += item.quantity;
                        });
                    }
                    updateBadges(totalCount);
                    window.dispatchEvent(new CustomEvent('cartUpdated'));
                }
            })
            .catch(e => console.error("Error syncing cart:", e));
    }

    // Bind event listeners for dynamic cart buttons
    if (!window.__mseDelegationBound) {
        window.__mseDelegationBound = true;
        document.addEventListener('click', function(e) {
            const addCartBtn = e.target.closest('.add-to-cart-btn');
            if (addCartBtn) {
                if (addCartBtn.id === 'addToCartBtn') {
                    return;
                }
                e.preventDefault();
                e.stopPropagation();
                console.log("Button clicked! (Add to Cart Card)");
                const id = addCartBtn.dataset.id || addCartBtn.getAttribute('data-id');
                const qty = parseInt(addCartBtn.dataset.qty || addCartBtn.getAttribute('data-qty')) || 1;
                const variant = addCartBtn.dataset.variant || addCartBtn.getAttribute('data-variant') || null;
                if (id) {
                    const originalHtml = addCartBtn.innerHTML;
                    addCartBtn.disabled = true;
                    addCartBtn.innerHTML = '<i data-lucide="check" style="width:14px;height:14px;"></i> Added!';
                    if (typeof lucide !== 'undefined') {
                        try { lucide.createIcons(); } catch (err) {}
                    }
                    setTimeout(() => {
                        addCartBtn.disabled = false;
                        addCartBtn.innerHTML = originalHtml;
                        if (typeof lucide !== 'undefined') {
                            try { lucide.createIcons(); } catch (err) {}
                        }
                    }, 1400);

                    addToCart(id, qty, variant);
                }
            }
        });
    }

    // Expose helpers globally for page specific templates
    window.mseWishlist = { get: () => [], toggle: () => false, init: () => {}, sync: () => {} };
    window.mseCart = { get: getCart, add: addToCart, remove: removeFromCart, updateQty: updateCartQty, sync: syncStatesWithDatabase };
    window.mseBadges = { update: updateBadges };
    window.showCartToast = showCartToast;

    // Mobile Search Bar Toggle
    const searchMobileToggle = document.getElementById('searchMobileToggle');
    const searchContainer = document.querySelector('.search-container');
    if (searchMobileToggle && searchContainer) {
        searchMobileToggle.addEventListener('click', function() {
            searchContainer.classList.toggle('active');
            if (searchContainer.classList.contains('active')) {
                const input = searchContainer.querySelector('.search-input');
                if (input) input.focus();
            }
        });
    }



    // PWA "Add to Home Screen" Bar dismiss/trigger
    const pwaHomeBar = document.getElementById('pwaHomeBar');
    const pwaCloseBtn = document.getElementById('pwaCloseBtn');
    if (pwaCloseBtn && pwaHomeBar) {
        pwaCloseBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            pwaHomeBar.classList.add('dismissed');
            sessionStorage.setItem('pwa_dismissed', 'true');
        });
    }
    
    if (pwaHomeBar && sessionStorage.getItem('pwa_dismissed') === 'true') {
        pwaHomeBar.classList.add('dismissed');
    }
    
    if (pwaHomeBar) {
        pwaHomeBar.addEventListener('click', function(e) {
            if (e.target !== pwaCloseBtn && !pwaCloseBtn.contains(e.target)) {
                alert("To Add MS Enterprises to your Home Screen: \n\n1. On Android/Chrome, tap the menu (three dots) and select 'Add to Home screen'. \n2. On iOS/Safari, click the Share icon and select 'Add to Home Screen'.");
            }
        });
    }

    // Render Recently Viewed section dynamically (loaded from database)
    function renderRecentlyViewed() {
        const recentlyViewedSection = document.getElementById('recentlyViewedSection');
        const recentlyViewedGrid = document.getElementById('recentlyViewedGrid');
        if (!recentlyViewedSection || !recentlyViewedGrid) return;

        fetch('/api/recently_viewed')
        .then(res => res.json())
        .then(data => {
            if (!data.success || !data.items || data.items.length === 0) {
                recentlyViewedGrid.innerHTML = '';
                recentlyViewedSection.style.display = 'none';
                return;
            }

            const products = data.items;
            recentlyViewedGrid.innerHTML = '';
            products.forEach(prod => {
                const card = document.createElement('div');
                card.className = 'product-card';

                let badgeHtml = '';
                if (prod.offer_price) {
                    const discount = Math.round(((prod.price - prod.offer_price) / prod.price) * 100);
                    if (discount > 0) {
                        badgeHtml += `<span class="badge badge-offer">${discount}% OFF</span>`;
                    }
                } else if (prod.offer_badge) {
                    badgeHtml += `<span class="badge badge-offer">${prod.offer_badge}</span>`;
                }
                if (prod.is_new_arrival) {
                    badgeHtml += `<span class="badge badge-new">New</span>`;
                }

                card.innerHTML = `
                    <div class="product-badge-container">
                        ${badgeHtml}
                    </div>
                    <a href="/product/${prod.slug}" class="product-card-img-wrapper">
                        <img src="${prod.image_url}" alt="${prod.name}" loading="lazy" onerror="this.onerror=null;this.src='/static/uploads/products/prod_generic_1.webp';">
                    </a>
                    <div class="product-card-body">
                        <span class="product-card-category">${prod.category_name}</span>
                        <h3 class="product-card-title"><a href="/product/${prod.slug}">${prod.name}</a></h3>
                        <div class="product-card-rating">
                            <span class="rating-stars">★ ${((prod.id % 7) / 10 + 4.3).toFixed(1)}</span>
                            <span class="rating-count">(${((prod.id * 13) % 40 + 8)})</span>
                        </div>
                        <p class="product-card-description">${prod.short_description || ''}</p>
                        <div class="product-card-pricing">
                            <span class="price-current">₹${priceCurrent.toLocaleString('en-IN')}</span>
                            ${priceOriginalHtml}
                        </div>
                        <div class="product-card-actions" style="width: 100%;">
                            <a href="/product/${prod.slug}" class="btn btn-dark btn-sm" style="width: 100%; text-align: center; display: flex; align-items: center; justify-content: center; gap: 6px;">View Details</a>
                        </div>
                    </div>
                `;
                recentlyViewedGrid.appendChild(card);
            });

            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            recentlyViewedSection.style.display = 'block';
        })
        .catch(err => {
            console.error("Error loading recently viewed products:", err);
            recentlyViewedSection.style.display = 'none';
        });
    }

    // ==========================================
    // 16. Scroll Preservation on Product Filter & Page Reload
    // ==========================================
    const catalogLayout = document.querySelector('.catalog-layout');
    if (catalogLayout) {
        // Restore scroll position if saved
        const savedScroll = sessionStorage.getItem('preserveCatalogScroll');
        if (savedScroll) {
            sessionStorage.removeItem('preserveCatalogScroll');
            // Use setTimeout to ensure grid rendering and layout stabilization before scrolling
            setTimeout(function() {
                window.scrollTo({
                    top: parseInt(savedScroll),
                    behavior: 'auto'
                });
            }, 50);
        }

        const saveScrollPosition = function() {
            sessionStorage.setItem('preserveCatalogScroll', window.scrollY);
        };

        // 1. Listen for filter sidebar form submit
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', saveScrollPosition);
        }

        // Also check for category search form or general sidebar forms
        const sidebarForm = document.querySelector('.filter-sidebar form');
        if (sidebarForm && sidebarForm !== filterForm) {
            sidebarForm.addEventListener('submit', saveScrollPosition);
        }

        // 2. Listen for category/subcategory filter link clicks
        document.querySelectorAll('.filter-link').forEach(link => {
            link.addEventListener('click', saveScrollPosition);
        });

        // 3. Listen for checkbox changes (triggers form submits)
        document.querySelectorAll('.filter-sidebar input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', saveScrollPosition);
        });

        // 4. Listen for sort selector dropdown change
        const sortSelect = document.getElementById('sortSelect') || document.querySelector('.sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', saveScrollPosition);
        }

        // 5. Listen for pagination link clicks
        document.querySelectorAll('.pagination-container a').forEach(link => {
            link.addEventListener('click', saveScrollPosition);
        });

        // 6. Listen for sort option helper dispatchers (in products.html / category.html)
        window.addEventListener('beforeunload', function() {
            // As a final safety fallback, if the active element is a select, checkbox or pagination link, save scroll
            const activeEl = document.activeElement;
            if (activeEl && (activeEl.tagName === 'SELECT' || activeEl.closest('.pagination-container') || activeEl.closest('.filter-sidebar'))) {
                saveScrollPosition();
            }
        });
    }

    // ==========================================
    // 17. Real-Time Catalogue Updates Checker
    // ==========================================
    let lastKnownUpdateTime = null;

    function checkForUpdates() {
        fetch('/api/updates/check')
            .then(res => res.json())
            .then(data => {
                if (data.success && data.last_updated) {
                    if (lastKnownUpdateTime === null) {
                        // Initialize last known update time on page load
                        lastKnownUpdateTime = data.last_updated;
                    } else if (lastKnownUpdateTime !== data.last_updated) {
                        // The database has been modified!
                        lastKnownUpdateTime = data.last_updated;
                        
                        // Notify user with a premium Toast or reload states
                        showLiveUpdateNotification();
                    }
                }
            })
            .catch(err => console.warn("Updates check failed:", err));
    }

    function showLiveUpdateNotification() {
        let banner = document.getElementById('liveUpdateBanner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'liveUpdateBanner';
            banner.style.cssText = `
                position: fixed;
                top: 24px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #111111;
                color: #FFFFFF;
                padding: 14px 28px;
                border-radius: var(--border-radius);
                border: 2px solid var(--accent-color);
                box-shadow: 0 15px 40px rgba(0,0,0,0.3);
                z-index: 100000;
                font-family: var(--font-heading);
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 16px;
                animation: slideDown 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            `;
            
            if (!document.getElementById('liveAnimStyles')) {
                const style = document.createElement('style');
                style.id = 'liveAnimStyles';
                style.innerHTML = `
                    @keyframes slideDown {
                        from { transform: translate(-50%, -50px); opacity: 0; }
                        to { transform: translate(-50%, 0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(banner);
        }
        
        banner.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="pulse-dot" style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:#25D366; animation: pulse 1.5s infinite;"></span>
                <span>The catalogue was updated live!</span>
            </div>
            <button id="liveUpdateBtn" class="btn btn-primary btn-sm" style="padding: 6px 12px; font-size:12px; margin-left:8px;">Refresh View</button>
        `;
        
        document.getElementById('liveUpdateBtn').addEventListener('click', function() {
            banner.style.display = 'none';
            syncStatesWithDatabase();
            if (document.querySelector('.catalog-layout')) {
                sessionStorage.setItem('preserveCatalogScroll', window.scrollY);
                window.location.reload();
            } else {
                window.location.reload();
            }
        });
    }

    // Initial load
    updateBadges();
    syncStatesWithDatabase(); // Sync cart with database on load
    renderRecentlyViewed();
    
    // Check for real-time catalogue updates every 15 seconds
    checkForUpdates();
    setInterval(checkForUpdates, 15000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMainApp);
} else {
    initMainApp();
}
window.addEventListener('load', initMainApp);

// Testimonials Public Submission Form helpers
window.openTestimonialForm = function() {
    const container = document.getElementById('testimonialFormContainer');
    if (container) {
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth' });
    }
};

window.closeTestimonialForm = function() {
    const container = document.getElementById('testimonialFormContainer');
    if (container) {
        container.style.display = 'none';
        document.getElementById('testimonialSubmitForm').reset();
        const statusDiv = document.getElementById('tFormStatus');
        if (statusDiv) statusDiv.style.display = 'none';
    }
};

window.submitTestimonialReview = function(event) {
    event.preventDefault();
    const name = document.getElementById('tFormName').value.trim();
    const city = document.getElementById('tFormCity').value.trim();
    const rating = parseInt(document.getElementById('tFormRating').value);
    const review = document.getElementById('tFormReviewText').value.trim();
    const statusDiv = document.getElementById('tFormStatus');
    
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.color = 'var(--primary-color)';
        statusDiv.innerText = 'Submitting your review...';
    }
    
    fetch('/api/testimonials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            customer_name: name,
            city: city,
            rating: rating,
            review: review
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            statusDiv.style.color = '#27AE60';
            statusDiv.innerText = data.message;
            setTimeout(() => {
                closeTestimonialForm();
            }, 3000);
        } else {
            statusDiv.style.color = '#E74C3C';
            statusDiv.innerText = data.message || 'Error submitting review.';
        }
    })
    .catch(err => {
        console.error("Testimonial submit error:", err);
        if (statusDiv) {
            statusDiv.style.color = '#E74C3C';
            statusDiv.innerText = 'Failed to submit review due to server error.';
        }
    });
};
