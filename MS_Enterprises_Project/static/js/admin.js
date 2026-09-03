// Admin Dashboard Logic & AJAX Controllers for MS Enterprises

// 0. Global Tab Navigation Function (immediately accessible to all HTML onclick handlers)
window.switchTab = function(tabId) {
    if (!tabId) return;
    const navButtons = document.querySelectorAll('.admin-nav-btn');
    const tabPanels = document.querySelectorAll('.admin-tab-panel');
    
    navButtons.forEach(btn => {
        if (btn.dataset.tab === tabId) btn.classList.add('active');
        else btn.classList.remove('active');
    });

    tabPanels.forEach(panel => {
        if (panel.id === tabId) panel.classList.add('active');
        else panel.classList.remove('active');
    });
    
    try {
        sessionStorage.setItem('admin_active_tab', tabId);
    } catch (e) {
        console.error("sessionStorage error:", e);
    }

    // Automatically trigger tab-specific data loaders when active
    if (tabId === 'tab-dealers' && typeof window.loadDealers === 'function') window.loadDealers();
    if (tabId === 'tab-dealer-activities' && typeof window.loadActivityLogs === 'function') window.loadActivityLogs();
    if (tabId === 'tab-dealer-orders' && typeof window.loadDealerOrders === 'function') window.loadDealerOrders();
    if (tabId === 'tab-orders' && typeof window.loadCustomerOrders === 'function') window.loadCustomerOrders();
    if (tabId === 'tab-stock-notifications' && typeof window.loadStockNotifications === 'function') window.loadStockNotifications();
};

document.addEventListener("DOMContentLoaded", function () {
    // 1. Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Set initial tab on load
    const activeTab = sessionStorage.getItem('admin_active_tab') || 'tab-overview';
    window.switchTab(activeTab);

    // 3. Alert Helper
    window.showAlert = function(type, message) {
        const alertBox = document.getElementById('dashboardAlert');
        if (alertBox) {
            alertBox.style.display = 'block';
            alertBox.className = `dashboard-alert ${type}`;
            alertBox.innerText = message;
            
            // Scroll to top of content
            document.querySelector('.admin-content-area').scrollTop = 0;
            
            setTimeout(() => {
                alertBox.style.display = 'none';
            }, 6000);
        }
    };

    // 4. Async Image Upload Trigger
    window.uploadImage = function(fileInput, targetInputId) {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        const alertBox = document.getElementById('dashboardAlert');
        showAlert('success', 'Uploading image file...');

        fetch('/api/admin/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById(targetInputId).value = data.url;
                showAlert('success', 'Image uploaded successfully!');
            } else {
                showAlert('error', 'Upload failed: ' + data.message);
            }
        })
        .catch(err => {
            console.error("Image upload AJAX error:", err);
            showAlert('error', 'Image upload failed due to server error.');
        });
    };

    window.uploadHeroImage = function(fileInput) {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        showAlert('success', 'Uploading image file...');

        fetch('/api/admin/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('heroFormImg').value = data.url;
                const imgPreview = document.getElementById('heroFormImgPreview');
                imgPreview.src = data.url;
                imgPreview.style.display = 'block';
                showAlert('success', 'Image uploaded successfully!');
            } else {
                showAlert('error', 'Upload failed: ' + data.message);
            }
        })
        .catch(err => {
            console.error("Hero image upload AJAX error:", err);
            showAlert('error', 'Image upload failed due to server error.');
        });
    };

    // 5. Global Settings save controller
    const settingsForm = document.getElementById('settingsSaveForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function (e) {
            e.preventDefault();

            let rawCountdownEnd = document.getElementById('settCountdownEndDate').value; // YYYY-MM-DDTHH:MM
            let formattedCountdownEnd = '';
            if (rawCountdownEnd) {
                formattedCountdownEnd = rawCountdownEnd.replace('T', ' ');
                if (formattedCountdownEnd.length === 16) {
                    formattedCountdownEnd += ':00';
                }
            }

            const settingsData = {
                whatsapp_number: document.getElementById('settWhatsapp').value.trim(),
                upi_id: document.getElementById('settUpi') ? document.getElementById('settUpi').value.trim() : '9676667998@ybl',
                contact_phone: document.getElementById('settPhone').value.trim(),
                contact_email: document.getElementById('settEmail').value.trim(),
                working_hours: document.getElementById('settHours').value.trim(),
                contact_address: document.getElementById('settAddress').value.trim(),
                google_map_link: document.getElementById('settMap').value.trim(),
                instagram_url: document.getElementById('settInsta').value.trim(),
                facebook_url: document.getElementById('settFb').value.trim(),
                youtube_url: document.getElementById('settYt').value.trim(),
                about_story: document.getElementById('settStory').value.trim(),
                about_mission: document.getElementById('settMission').value.trim(),
                about_vision: document.getElementById('settVision').value.trim(),
                seo_meta_title: document.getElementById('settSeoTitle').value.trim(),
                seo_meta_description: document.getElementById('settSeoDesc').value.trim(),
                new_password: document.getElementById('settNewPass').value.trim(),
                wishlist_enabled: document.getElementById('settWishlistEnabled').checked,
                cart_enabled: document.getElementById('settCartEnabled').checked,
                cart_min_value: parseFloat(document.getElementById('settCartMinValue').value || 0.0),
                standard_delivery_days: parseInt(document.getElementById('settStandardDeliveryDays') ? document.getElementById('settStandardDeliveryDays').value : 5, 10) || 5,
                preorder_delivery_days: parseInt(document.getElementById('settPreorderDeliveryDays') ? document.getElementById('settPreorderDeliveryDays').value : 15, 10) || 15,
                whatsapp_wishlist_prefix: document.getElementById('settWhatsappWishlistPrefix').value.trim(),
                whatsapp_cart_prefix: document.getElementById('settWhatsappCartPrefix').value.trim(),
                countdown_enabled: document.getElementById('settCountdownEnabled').checked,
                countdown_end_date: formattedCountdownEnd
            };

            fetch('/api/admin/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    document.getElementById('settNewPass').value = ''; // clear password input
                } else {
                    showAlert('error', 'Failed: ' + data.message);
                }
            })
            .catch(err => {
                console.error("Settings save error:", err);
                showAlert('error', 'Internal server error saving settings.');
            });
        });
    }

    // 5b. Social Settings save controller
    const socialForm = document.getElementById('socialSaveForm');
    if (socialForm) {
        socialForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitBtn = socialForm.querySelector('button[type="submit"]');
            const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Saving...';
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }

            const socialData = {
                facebook_url: document.getElementById('settFbSocial').value.trim(),
                instagram_url: document.getElementById('settInstaSocial').value.trim(),
                youtube_url: document.getElementById('settYtSocial').value.trim(),
                show_facebook: document.getElementById('settFbShow').checked,
                show_instagram: document.getElementById('settInstaShow').checked,
                show_youtube: document.getElementById('settYtShow').checked
            };

            fetch('/api/admin/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(socialData)
            })
            .then(res => res.json())
            .then(data => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }

                if (data.success) {
                    // Sync values across settings form inputs if present
                    if (document.getElementById('settFb')) document.getElementById('settFb').value = socialData.facebook_url;
                    if (document.getElementById('settInsta')) document.getElementById('settInsta').value = socialData.instagram_url;
                    if (document.getElementById('settYt')) document.getElementById('settYt').value = socialData.youtube_url;

                    showAlert('success', data.message || 'Social media settings saved successfully!');
                } else {
                    showAlert('error', 'Failed: ' + (data.message || 'Could not save settings.'));
                }
            })
            .catch(err => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
                console.error("Social settings save error:", err);
                showAlert('error', 'Internal server error saving social media settings.');
            });
        });
    }

    // 6. Review approval logic
    window.approveReview = function(id) {
        if (!confirm("Are you sure you want to approve this customer review? It will appear publicly on the live website immediately.")) return;

        fetch('/api/admin/reviews', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, status: 'approved' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Review approved successfully!');
                setTimeout(() => window.location.reload(), 600);
            } else {
                showAlert('error', data.message || 'Failed to approve review.');
            }
        })
        .catch(err => {
            console.error("Approve review error:", err);
            showAlert('error', 'Server error approving review.');
        });
    };

    window.rejectReview = function(id) {
        if (!confirm("Are you sure you want to reject this customer review? It will remain hidden from the public website.")) return;

        fetch('/api/admin/reviews', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, status: 'rejected' })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Review rejected successfully.');
                setTimeout(() => window.location.reload(), 600);
            } else {
                showAlert('error', data.message || 'Failed to reject review.');
            }
        })
        .catch(err => {
            console.error("Reject review error:", err);
            showAlert('error', 'Server error rejecting review.');
        });
    };

    window.deleteReview = function(id) {
        if (!confirm("Are you sure you want to permanently delete this customer review?")) return;

        fetch(`/api/admin/reviews?id=${id}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Review deleted successfully!');
                setTimeout(() => window.location.reload(), 600);
            } else {
                showAlert('error', data.message || 'Failed to delete review.');
            }
        })
        .catch(err => {
            console.error("Delete review error:", err);
            showAlert('error', 'Server error deleting review.');
        });
    };

    // 7. Product Modal List Builders (Specs, highlights, variants)
    window.addSpecRow = function(key = '', val = '') {
        const container = document.getElementById('specsContainer');
        const div = document.createElement('div');
        div.className = 'spec-row';
        div.style.display = 'flex';
        div.style.gap = '10px';
        div.innerHTML = `
            <input type="text" placeholder="Spec key (e.g. Dimensions)" class="form-control spec-key" value="${key}" required style="flex:1;">
            <input type="text" placeholder="Spec value (e.g. 72 x 36 inches)" class="form-control spec-val" value="${val}" required style="flex:1;">
            <button type="button" class="btn btn-dark btn-sm" onclick="this.parentElement.remove()" style="padding:10px; background:#E74C3C; border-color:#E74C3C;"><i data-lucide="trash-2" style="width:14px;height:14px;"></i></button>
        `;
        container.appendChild(div);
        lucide.createIcons();
    };

    window.addFeatureRow = function(feat = '') {
        const container = document.getElementById('featuresContainer');
        const div = document.createElement('div');
        div.className = 'feature-row';
        div.style.display = 'flex';
        div.style.gap = '10px';
        div.innerHTML = `
            <input type="text" placeholder="Product highlight feature text" class="form-control feature-text" value="${feat}" required style="flex:1;">
            <button type="button" class="btn btn-dark btn-sm" onclick="this.parentElement.remove()" style="padding:10px; background:#E74C3C; border-color:#E74C3C;"><i data-lucide="trash-2" style="width:14px;height:14px;"></i></button>
        `;
        container.appendChild(div);
        lucide.createIcons();
    };

    window.addVariantRow = function(name = '', val = '', adjust = '0.0') {
        const container = document.getElementById('variantsContainer');
        const div = document.createElement('div');
        div.className = 'variant-row';
        div.style.display = 'flex';
        div.style.gap = '10px';
        div.innerHTML = `
            <input type="text" placeholder="Type (e.g. Material)" class="form-control var-name" value="${name}" required style="flex:1;">
            <input type="text" placeholder="Value (e.g. Teak Wood)" class="form-control var-val" value="${val}" required style="flex:1;">
            <input type="number" step="100" placeholder="Price adjust (+/-)" class="form-control var-adjust" value="${adjust}" required style="width:140px;">
            <button type="button" class="btn btn-dark btn-sm" onclick="this.parentElement.remove()" style="padding:10px; background:#E74C3C; border-color:#E74C3C;"><i data-lucide="trash-2" style="width:14px;height:14px;"></i></button>
        `;
        container.appendChild(div);
        lucide.createIcons();
    };

    // 8. Populate Subcategories in Product Form
    window.populateSubcategories = function(subcatIdToSelect = null) {
        const catSelect = document.getElementById('prodFormCat');
        const subSelect = document.getElementById('prodFormSub');
        const catId = catSelect.value;

        subSelect.innerHTML = '<option value="">Select Subcategory</option>';
        if (!catId) return;

        const subLookupList = document.querySelectorAll('#subcatLookupData span');
        subLookupList.forEach(span => {
            const pCatId = span.dataset.catId;
            if (pCatId === catId) {
                const opt = document.createElement('option');
                opt.value = span.dataset.id;
                opt.innerText = span.dataset.name;
                if (subcatIdToSelect && span.dataset.id === String(subcatIdToSelect)) {
                    opt.selected = true;
                }
                subSelect.appendChild(opt);
            }
        });
    };

    // 9. Product Modal Toggles
    const prodModal = document.getElementById('prodModal');
    window.openProductModal = function() {
        document.getElementById('prodForm').reset();
        document.getElementById('formProdId').value = '';
        document.getElementById('prodModalTitle').innerText = 'Add Product Catalog Item';
        document.getElementById('specsContainer').innerHTML = '';
        document.getElementById('featuresContainer').innerHTML = '';
        document.getElementById('variantsContainer').innerHTML = '';
        
        // Add one empty row for features and specs
        addSpecRow('Material', 'Premium Teak Wood');
        addFeatureRow('Premium craftsmanship with factory direct price.');
        
        // Default inventory values
        if (document.getElementById('prodFormStockStatus')) document.getElementById('prodFormStockStatus').value = 'in_stock';
        if (document.getElementById('prodFormStockQuantity')) document.getElementById('prodFormStockQuantity').value = '10';
        if (document.getElementById('prodFormAllowPreorder')) document.getElementById('prodFormAllowPreorder').checked = false;

        populateSubcategories();
        prodModal.classList.add('active');
    };

    window.closeProductModal = function() {
        prodModal.classList.remove('active');
    };

    // 10. Product CRUD Operations
    const prodForm = document.getElementById('prodForm');
    if (prodForm) {
        prodForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // Extract specifications
            const specs = {};
            document.querySelectorAll('#specsContainer .spec-row').forEach(row => {
                const k = row.querySelector('.spec-key').value.trim();
                const v = row.querySelector('.spec-val').value.trim();
                if (k && v) specs[k] = v;
            });

            // Extract features
            const features = [];
            document.querySelectorAll('#featuresContainer .feature-row').forEach(row => {
                const f = row.querySelector('.feature-text').value.trim();
                if (f) features.push(f);
            });

            // Extract variants
            const variants = [];
            document.querySelectorAll('#variantsContainer .variant-row').forEach(row => {
                const name = row.querySelector('.var-name').value.trim();
                const value = row.querySelector('.var-val').value.trim();
                const price_adjustment = parseFloat(row.querySelector('.var-adjust').value || 0.0);
                if (name && value) {
                    variants.push({ name, value, price_adjustment });
                }
            });

            const productData = {
                id: document.getElementById('formProdId').value || null,
                name: document.getElementById('prodFormName').value.trim(),
                sku: document.getElementById('prodFormSku').value.trim(),
                category_id: parseInt(document.getElementById('prodFormCat').value),
                subcategory_id: parseInt(document.getElementById('prodFormSub').value) || null,
                price: parseFloat(document.getElementById('prodFormPrice').value),
                offer_price: parseFloat(document.getElementById('prodFormOfferPrice').value) || null,
                offer_badge: document.getElementById('prodFormBadge').value.trim(),
                short_description: document.getElementById('prodFormShortDesc').value.trim(),
                description: document.getElementById('prodFormDesc').value.trim(),
                status: document.getElementById('prodFormStatus').value,
                is_featured: document.getElementById('prodFormFeat').checked,
                is_new_arrival: document.getElementById('prodFormNew').checked,
                is_best_seller: document.getElementById('prodFormBest').checked,
                is_premium: document.getElementById('prodFormPrem').checked,
                images: [
                    document.getElementById('prodFormImg1').value.trim(),
                    document.getElementById('prodFormImg2').value.trim(),
                    document.getElementById('prodFormImg3').value.trim()
                ].filter(Boolean),
                specifications: specs,
                features: features,
                variants: variants,
                wholesale_price: parseFloat(document.getElementById('prodFormWholesalePrice').value || 0.0),
                dealer_prices: {
                    default: parseFloat(document.getElementById('prodFormWholesalePrice').value) || 0.0,
                    silver: document.getElementById('prodFormWholesalePriceSilver').value.trim() !== '' ? parseFloat(document.getElementById('prodFormWholesalePriceSilver').value) : null,
                    gold: document.getElementById('prodFormWholesalePriceGold').value.trim() !== '' ? parseFloat(document.getElementById('prodFormWholesalePriceGold').value) : null,
                    platinum: document.getElementById('prodFormWholesalePricePlatinum').value.trim() !== '' ? parseFloat(document.getElementById('prodFormWholesalePricePlatinum').value) : null
                },
                dealer_status: document.getElementById('prodFormDealerStatus').value,
                stock_status: document.getElementById('prodFormStockStatus') ? document.getElementById('prodFormStockStatus').value : 'in_stock',
                stock_quantity: document.getElementById('prodFormStockQuantity') ? (parseInt(document.getElementById('prodFormStockQuantity').value) || 0) : 10,
                allow_preorder: document.getElementById('prodFormAllowPreorder') ? document.getElementById('prodFormAllowPreorder').checked : false
            };

            // Validation
            if (!productData.name) {
                showAlert('error', 'Product Name is a required field.');
                return;
            }
            if (isNaN(productData.category_id)) {
                showAlert('error', 'Please select a Category.');
                return;
            }
            if (isNaN(productData.price) || productData.price <= 0) {
                showAlert('error', 'Please enter a valid positive price.');
                return;
            }

            const method = productData.id ? 'PUT' : 'POST';
            const submitBtn = prodForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;

            // Set loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader" class="animate-spin" style="width:16px;height:16px;display:inline-block;margin-right:8px;"></i> Saving product...';
            if (typeof lucide !== 'undefined') lucide.createIcons();

            fetch('/api/admin/products', {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message || 'Product saved successfully!');
                    closeProductModal();
                    if (typeof loadProductsAndRedrawTable === 'function') {
                        loadProductsAndRedrawTable();
                    }
                } else {
                    showAlert('error', data.message);
                }
            })
            .catch(err => {
                console.error("Product save AJAX error:", err);
                showAlert('error', 'Server error saving product catalog.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            });
        });
    }

    window.editProduct = function(id) {
        fetch(`/api/admin/products?id=${id}`)
            .then(res => {
                if (!res.ok) throw new Error("Product data request failed.");
                return res.json();
            })
            .then(data => {
                if (data.id) {
                    document.getElementById('prodForm').reset();
                    document.getElementById('formProdId').value = data.id;
                    document.getElementById('prodModalTitle').innerText = 'Edit Product Catalog Item';
                    document.getElementById('prodFormName').value = data.name;
                    document.getElementById('prodFormSku').value = data.sku || '';
                    document.getElementById('prodFormCat').value = data.category_id;
                    
                    populateSubcategories(data.subcategory_id);
                    
                    document.getElementById('prodFormPrice').value = data.price;
                    document.getElementById('prodFormOfferPrice').value = data.offer_price || '';
                    document.getElementById('prodFormBadge').value = data.offer_badge || '';
                    
                    // Load B2B attributes
                    const dp = data.dealer_prices || {};
                    document.getElementById('prodFormWholesalePrice').value = dp.default !== null && dp.default !== undefined ? dp.default : 0.0;
                    document.getElementById('prodFormWholesalePriceSilver').value = dp.silver !== null && dp.silver !== undefined ? dp.silver : '';
                    document.getElementById('prodFormWholesalePriceGold').value = dp.gold !== null && dp.gold !== undefined ? dp.gold : '';
                    document.getElementById('prodFormWholesalePricePlatinum').value = dp.platinum !== null && dp.platinum !== undefined ? dp.platinum : '';
                    document.getElementById('prodFormDealerStatus').value = data.dealer_status || 'visible';

                    // Load Inventory attributes
                    if (document.getElementById('prodFormStockStatus')) {
                        document.getElementById('prodFormStockStatus').value = data.stock_status || 'in_stock';
                    }
                    if (document.getElementById('prodFormStockQuantity')) {
                        document.getElementById('prodFormStockQuantity').value = data.stock_quantity !== undefined && data.stock_quantity !== null ? data.stock_quantity : 10;
                    }
                    if (document.getElementById('prodFormAllowPreorder')) {
                        document.getElementById('prodFormAllowPreorder').checked = Boolean(data.allow_preorder == 1 || data.allow_preorder === true || data.allow_preorder === '1' || data.allow_preorder === 'true');
                    }

                    document.getElementById('prodFormShortDesc').value = data.short_description;
                    document.getElementById('prodFormDesc').value = data.description;
                    document.getElementById('prodFormStatus').value = data.status;
                    
                    document.getElementById('prodFormFeat').checked = Boolean(data.is_featured == 1 || data.is_featured === true || data.is_featured === '1');
                    document.getElementById('prodFormNew').checked = Boolean(data.is_new_arrival == 1 || data.is_new_arrival === true || data.is_new_arrival === '1');
                    document.getElementById('prodFormBest').checked = Boolean(data.is_best_seller == 1 || data.is_best_seller === true || data.is_best_seller === '1');
                    document.getElementById('prodFormPrem').checked = Boolean(data.is_premium == 1 || data.is_premium === true || data.is_premium === '1');

                    // Images
                    const imgs = data.images || [];
                    document.getElementById('prodFormImg1').value = imgs[0] || '';
                    document.getElementById('prodFormImg2').value = imgs[1] || '';
                    document.getElementById('prodFormImg3').value = imgs[2] || '';

                    // specs container
                    const specsContainer = document.getElementById('specsContainer');
                    specsContainer.innerHTML = '';
                    if (data.specifications) {
                        for (const [k, v] of Object.entries(data.specifications)) {
                            addSpecRow(k, v);
                        }
                    }

                    // features container
                    const featuresContainer = document.getElementById('featuresContainer');
                    featuresContainer.innerHTML = '';
                    if (data.features) {
                        data.features.forEach(f => {
                            addFeatureRow(f);
                        });
                    }

                    // variants container
                    const variantsContainer = document.getElementById('variantsContainer');
                    variantsContainer.innerHTML = '';
                    if (data.variants) {
                        data.variants.forEach(v => {
                            addVariantRow(v.name, v.value, v.price_adjustment);
                        });
                    }

                    prodModal.classList.add('active');
                }
            })
            .catch(err => {
                console.error("Error loading product edit details:", err);
                showAlert('error', 'Failed to retrieve product edit details.');
            });
    };

    window.duplicateProduct = function(id) {
        if (!confirm("Are you sure you want to duplicate this product? It will create a duplicate record in Draft mode.")) return;

        showAlert('success', 'Duplicating product...');
        fetch('/api/admin/products/duplicate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        })
        .then(res => {
            if (!res.ok) throw new Error("Duplication failed.");
            return res.json();
        })
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Product duplicated successfully!');
                if (typeof loadProductsAndRedrawTable === 'function') {
                    loadProductsAndRedrawTable();
                }
            } else {
                showAlert('error', data.message);
            }
        })
        .catch(err => {
            console.error("Product duplication error:", err);
            showAlert('error', 'Server error duplicating product.');
        });
    };

    window.deleteProduct = function(id) {
        if (!confirm("Are you sure you want to delete this product? This action is permanent!")) return;

        showAlert('success', 'Deleting product...');
        fetch(`/api/admin/products?id=${id}`, {
            method: 'DELETE'
        })
        .then(res => {
            if (!res.ok) throw new Error("Deletion failed.");
            return res.json();
        })
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Product deleted successfully.');
                if (typeof loadProductsAndRedrawTable === 'function') {
                    loadProductsAndRedrawTable();
                }
            } else {
                showAlert('error', data.message);
            }
        })
        .catch(err => {
            console.error("Product deletion error:", err);
            showAlert('error', 'Server error deleting product.');
        });
    };

    // 11. Category Modals & Operations
    const catModal = document.getElementById('catModal');
    window.openCategoryModal = function() {
        document.getElementById('catForm').reset();
        document.getElementById('formCatId').value = '';
        document.getElementById('catModalTitle').innerText = 'Add Category';
        catModal.classList.add('active');
    };
    window.closeCategoryModal = function() {
        catModal.classList.remove('active');
    };

    document.getElementById('catForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const catData = {
            id: document.getElementById('formCatId').value || null,
            name: document.getElementById('catFormName').value.trim(),
            image_url: document.getElementById('catFormImg').value.trim(),
            description: document.getElementById('catFormDesc').value.trim(),
            display_order: parseInt(document.getElementById('catFormOrder').value || 0),
            status: document.getElementById('catFormStatus').value
        };

        const method = catData.id ? 'PUT' : 'POST';
        fetch('/api/admin/categories', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(catData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeCategoryModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editCategory = function(id) {
        fetch(`/api/admin/categories?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formCatId').value = data.id;
                    document.getElementById('catModalTitle').innerText = 'Edit Category';
                    document.getElementById('catFormName').value = data.name;
                    document.getElementById('catFormImg').value = data.image_url;
                    document.getElementById('catFormDesc').value = data.description || '';
                    document.getElementById('catFormOrder').value = data.display_order;
                    document.getElementById('catFormStatus').value = data.status;
                    catModal.classList.add('active');
                }
            });
    };

    window.deleteCategory = function(id) {
        if (!confirm("Are you sure you want to delete this category? It will remove all links, but products will remain (uncategorized).")) return;
        fetch(`/api/admin/categories?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 12. Subcategory Modals & Operations
    const subModal = document.getElementById('subModal');
    window.openSubcategoryModal = function() {
        document.getElementById('subForm').reset();
        document.getElementById('formSubId').value = '';
        document.getElementById('subModalTitle').innerText = 'Add Subcategory';
        subModal.classList.add('active');
    };
    window.closeSubcategoryModal = function() {
        subModal.classList.remove('active');
    };

    document.getElementById('subForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const subData = {
            id: document.getElementById('formSubId').value || null,
            category_id: parseInt(document.getElementById('subFormCat').value),
            name: document.getElementById('subFormName').value.trim(),
            display_order: parseInt(document.getElementById('subFormOrder').value || 0),
            status: document.getElementById('subFormStatus').value
        };

        const method = subData.id ? 'PUT' : 'POST';
        fetch('/api/admin/subcategories', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeSubcategoryModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editSubcategory = function(id) {
        fetch(`/api/admin/subcategories?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formSubId').value = data.id;
                    document.getElementById('subModalTitle').innerText = 'Edit Subcategory';
                    document.getElementById('subFormCat').value = data.category_id;
                    document.getElementById('subFormName').value = data.name;
                    document.getElementById('subFormOrder').value = data.display_order;
                    document.getElementById('subFormStatus').value = data.status;
                    subModal.classList.add('active');
                }
            });
    };

    window.deleteSubcategory = function(id) {
        if (!confirm("Are you sure you want to delete this subcategory?")) return;
        fetch(`/api/admin/subcategories?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 13. Hero Banner Operations
    const heroModal = document.getElementById('heroModal');
    window.openHeroModal = function() {
        document.getElementById('heroForm').reset();
        document.getElementById('formHeroId').value = '';
        document.getElementById('heroModalTitle').innerText = 'Add Hero Slide';
        document.getElementById('heroFormImgPreview').style.display = 'none';
        document.getElementById('heroFormImgPreview').src = '';
        heroModal.classList.add('active');
    };
    window.closeHeroModal = function() {
        heroModal.classList.remove('active');
    };

    document.getElementById('heroForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const heroData = {
            id: document.getElementById('formHeroId').value || null,
            title: document.getElementById('heroFormTitle').value.trim(),
            subtitle: document.getElementById('heroFormSubtitle').value.trim(),
            image_url: document.getElementById('heroFormImg').value.trim(),
            link_text: document.getElementById('heroFormBtnText').value.trim(),
            link_url: document.getElementById('heroFormBtnLink').value.trim(),
            display_order: parseInt(document.getElementById('heroFormOrder').value || 0),
            status: document.getElementById('heroFormStatus').value
        };

        const method = heroData.id ? 'PUT' : 'POST';
        fetch('/api/admin/hero_banners', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(heroData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeHeroModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editHero = function(id) {
        fetch(`/api/admin/hero_banners?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formHeroId').value = data.id;
                    document.getElementById('heroModalTitle').innerText = 'Edit Hero Slide';
                    document.getElementById('heroFormTitle').value = data.title || '';
                    document.getElementById('heroFormSubtitle').value = data.subtitle || '';
                    document.getElementById('heroFormImg').value = data.image_url;
                    
                    const imgPreview = document.getElementById('heroFormImgPreview');
                    if (data.image_url) {
                        imgPreview.src = data.image_url;
                        imgPreview.style.display = 'block';
                    } else {
                        imgPreview.style.display = 'none';
                    }

                    document.getElementById('heroFormBtnText').value = data.link_text || '';
                    document.getElementById('heroFormBtnLink').value = data.link_url || '';
                    document.getElementById('heroFormOrder').value = data.display_order;
                    document.getElementById('heroFormStatus').value = data.status;
                    heroModal.classList.add('active');
                }
            });
    };

    window.deleteHero = function(id) {
        if (!confirm("Are you sure you want to delete this hero slide?")) return;
        fetch(`/api/admin/hero_banners?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 14. Offer Banner Operations
    const offerModal = document.getElementById('offerModal');
    window.openOfferModal = function() {
        document.getElementById('offerForm').reset();
        document.getElementById('formOfferId').value = '';
        document.getElementById('offerModalTitle').innerText = 'Add Offer Banner';
        offerModal.classList.add('active');
    };
    window.closeOfferModal = function() {
        offerModal.classList.remove('active');
    };

    document.getElementById('offerForm').addEventListener('submit', function (e) {
        e.preventDefault();
        
        let rawEndingDate = document.getElementById('offerFormEnding').value; // YYYY-MM-DDTHH:MM
        let formattedEndingDate = '';
        if (rawEndingDate) {
            formattedEndingDate = rawEndingDate.replace('T', ' ');
            if (formattedEndingDate.length === 16) {
                formattedEndingDate += ':00'; // Append seconds
            }
        }

        const offerData = {
            id: document.getElementById('formOfferId').value || null,
            title: document.getElementById('offerFormTitle').value.trim(),
            subtitle: document.getElementById('offerFormSubtitle').value.trim(),
            image_url: document.getElementById('offerFormImg').value.trim(),
            ending_date: formattedEndingDate,
            button_text: document.getElementById('offerFormBtnText').value.trim(),
            button_link: document.getElementById('offerFormBtnLink').value.trim(),
            status: document.getElementById('offerFormStatus').value
        };

        const method = offerData.id ? 'PUT' : 'POST';
        fetch('/api/admin/offer_banners', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(offerData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeOfferModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editOffer = function(id) {
        fetch(`/api/admin/offer_banners?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formOfferId').value = data.id;
                    document.getElementById('offerModalTitle').innerText = 'Edit Offer Banner';
                    document.getElementById('offerFormTitle').value = data.title;
                    document.getElementById('offerFormSubtitle').value = data.subtitle || '';
                    document.getElementById('offerFormImg').value = data.image_url;
                    
                    let endingVal = data.ending_date || '';
                    if (endingVal) {
                        endingVal = endingVal.replace(' ', 'T');
                        if (endingVal.length > 16) {
                            endingVal = endingVal.substring(0, 16);
                        }
                    }
                    document.getElementById('offerFormEnding').value = endingVal;
                    
                    document.getElementById('offerFormBtnText').value = data.button_text || '';
                    document.getElementById('offerFormBtnLink').value = data.button_link || '';
                    document.getElementById('offerFormStatus').value = data.status;
                    offerModal.classList.add('active');
                }
            });
    };

    window.deleteOffer = function(id) {
        if (!confirm("Are you sure you want to delete this offer banner?")) return;
        fetch(`/api/admin/offer_banners?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 15. Testimonial Operations
    const testimonialModal = document.getElementById('testimonialModal');
    window.openTestimonialModal = function() {
        document.getElementById('testimonialForm').reset();
        document.getElementById('formTestId').value = '';
        document.getElementById('testimonialModalTitle').innerText = 'Add Testimonial';
        testimonialModal.classList.add('active');
    };
    window.closeTestimonialModal = function() {
        testimonialModal.classList.remove('active');
    };

    document.getElementById('testimonialForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const testData = {
            id: document.getElementById('formTestId').value || null,
            customer_name: document.getElementById('testFormName').value.trim(),
            customer_photo: document.getElementById('testFormPhoto').value.trim(),
            city: document.getElementById('testFormCity').value.trim(),
            rating: parseInt(document.getElementById('testFormRating').value),
            review: document.getElementById('testFormReview').value.trim(),
            status: document.getElementById('testFormStatus').value
        };

        const method = testData.id ? 'PUT' : 'POST';
        fetch('/api/admin/testimonials', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeTestimonialModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editTestimonial = function(id) {
        fetch(`/api/admin/testimonials?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formTestId').value = data.id;
                    document.getElementById('testimonialModalTitle').innerText = 'Edit Testimonial';
                    document.getElementById('testFormName').value = data.customer_name;
                    document.getElementById('testFormPhoto').value = data.customer_photo || '';
                    document.getElementById('testFormCity').value = data.city;
                    document.getElementById('testFormRating').value = data.rating;
                    document.getElementById('testFormReview').value = data.review;
                    document.getElementById('testFormStatus').value = data.status;
                    testimonialModal.classList.add('active');
                }
            });
    };

    window.deleteTestimonial = function(id) {
        if (!confirm("Are you sure you want to delete this testimonial?")) return;
        fetch(`/api/admin/testimonials?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 16. Video Operations
    const videoModal = document.getElementById('videoModal');
    window.openVideoModal = function() {
        document.getElementById('videoForm').reset();
        document.getElementById('formVideoId').value = '';
        document.getElementById('videoModalTitle').innerText = 'Add Video';
        videoModal.classList.add('active');
    };
    window.closeVideoModal = function() {
        videoModal.classList.remove('active');
    };

    document.getElementById('videoForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const videoData = {
            id: document.getElementById('formVideoId').value || null,
            customer_name: document.getElementById('videoFormName').value.trim(),
            video_url: document.getElementById('videoFormUrl').value.trim(),
            thumbnail_url: document.getElementById('videoFormThumb').value.trim(),
            review_text: document.getElementById('videoFormDesc').value.trim(),
            status: document.getElementById('videoFormStatus').value
        };

        const method = videoData.id ? 'PUT' : 'POST';
        fetch('/api/admin/videos', {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(videoData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                closeVideoModal();
                window.location.reload();
            } else {
                showAlert('error', data.message);
            }
        });
    });

    window.editVideo = function(id) {
        fetch(`/api/admin/videos?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('formVideoId').value = data.id;
                    document.getElementById('videoModalTitle').innerText = 'Edit Video';
                    document.getElementById('videoFormName').value = data.customer_name;
                    document.getElementById('videoFormUrl').value = data.video_url;
                    document.getElementById('videoFormThumb').value = data.thumbnail_url || '';
                    document.getElementById('videoFormDesc').value = data.review_text;
                    document.getElementById('videoFormStatus').value = data.status;
                    videoModal.classList.add('active');
                }
            });
    };

    window.deleteVideo = function(id) {
        if (!confirm("Are you sure you want to delete this video testimonial?")) return;
        fetch(`/api/admin/videos?id=${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.reload();
                else showAlert('error', data.message);
            });
    };

    // 17. Fast table filtering logic
    window.filterTable = function(inputId, tableId) {
        const input = document.getElementById(inputId);
        const filter = input.value.toLowerCase();
        const table = document.getElementById(tableId);
        const tr = table.getElementsByTagName("tr");

        for (let i = 1; i < tr.length; i++) {
            let rowText = tr[i].textContent || tr[i].innerText;
            if (rowText.toLowerCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    };

    // 18. Category Banners Management
    const catBannersEditor = document.getElementById('catBannersEditor');
    
    window.loadCategoryBanners = function(categoryId) {
        if (!categoryId) {
            catBannersEditor.style.display = 'none';
            return;
        }

        // Load Hero Banner
        fetch(`/api/admin/category_hero_banners?category_id=${categoryId}`)
            .then(res => res.json())
            .then(heroBanner => {
                document.getElementById('chbCatId').value = categoryId;
                document.getElementById('chbTitle').value = heroBanner.title || '';
                document.getElementById('chbImg').value = heroBanner.image_url || '';
                document.getElementById('chbOfferText').value = heroBanner.offer_text || '';
                document.getElementById('chbBtnText').value = heroBanner.button_text || 'Explore Collection';
                document.getElementById('chbStatus').value = heroBanner.status || 'active';
            });

        // Load Offer Banner
        fetch(`/api/admin/category_offer_banners?category_id=${categoryId}`)
            .then(res => res.json())
            .then(offerBanner => {
                document.getElementById('cobCatId').value = categoryId;
                document.getElementById('cobTitle').value = offerBanner.title || '';
                document.getElementById('cobImg').value = offerBanner.image_url || '';
                document.getElementById('cobDiscount').value = offerBanner.discount || '';
                document.getElementById('cobProductImg').value = offerBanner.product_image_url || '';
                document.getElementById('cobProductPrice').value = offerBanner.product_price || '0';
                document.getElementById('cobStatus').value = offerBanner.status || 'active';
            });

        catBannersEditor.style.display = 'grid';
    };

    // Category Hero Form submit
    const catHeroBannerForm = document.getElementById('catHeroBannerForm');
    if (catHeroBannerForm) {
        catHeroBannerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const chbData = {
                category_id: parseInt(document.getElementById('chbCatId').value),
                title: document.getElementById('chbTitle').value.trim(),
                image_url: document.getElementById('chbImg').value.trim(),
                offer_text: document.getElementById('chbOfferText').value.trim(),
                button_text: document.getElementById('chbBtnText').value.trim(),
                status: document.getElementById('chbStatus').value
            };

            fetch('/api/admin/category_hero_banners', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(chbData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                } else {
                    showAlert('error', data.message);
                }
            });
        });
    }

    // Category Offer Form submit
    const catOfferBannerForm = document.getElementById('catOfferBannerForm');
    if (catOfferBannerForm) {
        catOfferBannerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const cobData = {
                category_id: parseInt(document.getElementById('cobCatId').value),
                title: document.getElementById('cobTitle').value.trim(),
                image_url: document.getElementById('cobImg').value.trim(),
                discount: document.getElementById('cobDiscount').value.trim(),
                product_image_url: document.getElementById('cobProductImg').value.trim(),
                product_price: parseFloat(document.getElementById('cobProductPrice').value || 0.0),
                status: document.getElementById('cobStatus').value
            };

            fetch('/api/admin/category_offer_banners', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cobData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                } else {
                    showAlert('error', data.message);
                }
            });
        });
    }

    // ----------------- B2B DEALER PORTAL JS CONTROLLERS -----------------
    
    let localActivityLogs = [];
    
    window.loadDealers = function() {
        const tbody = document.getElementById('dealersTableBody');
        if (!tbody) return;
        
        fetch('/api/admin/dealers')
            .then(res => res.json())
            .then(data => {
                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="padding:20px; text-align:center; color:var(--text-muted);">No dealer registrations found.</td></tr>';
                    return;
                }
                
                data.forEach(d => {
                    let statusColor = '#b45309';
                    if (d.status === 'approved') statusColor = '#16a34a';
                    if (d.status === 'suspended' || d.status === 'rejected') statusColor = '#dc2626';
                    
                    let statusBadge = `<span style="background:${statusColor}15; color:${statusColor}; font-weight:700; font-size:12px; padding:3px 8px; border-radius:4px; text-transform:uppercase;">${d.status}</span>`;
                    
                    let actions = '';
                    if (d.status === 'pending') {
                        actions += `<button class="btn btn-primary btn-sm" onclick="updateDealerStatus('${d.id}', 'approved')" style="background:#16a34a; border:none; padding:5px 10px; margin-right:5px; color:#fff; cursor:pointer;">Approve</button>`;
                        actions += `<button class="btn btn-primary btn-sm" onclick="updateDealerStatus('${d.id}', 'rejected')" style="background:#dc2626; border:none; padding:5px 10px; margin-right:5px; color:#fff; cursor:pointer;">Reject</button>`;
                    } else if (d.status === 'approved') {
                        actions += `<button class="btn btn-secondary btn-sm" onclick="updateDealerStatus('${d.id}', 'suspended')" style="padding:5px 10px; margin-right:5px; cursor:pointer;">Suspend</button>`;
                    } else if (d.status === 'suspended' || d.status === 'rejected') {
                        actions += `<button class="btn btn-primary btn-sm" onclick="updateDealerStatus('${d.id}', 'approved')" style="background:#16a34a; border:none; padding:5px 10px; margin-right:5px; color:#fff; cursor:pointer;">Activate</button>`;
                    }
                    actions += `<button class="btn btn-secondary btn-sm" onclick="deleteDealer('${d.id}')" style="padding:5px 10px; color:#dc2626; border-color:#fca5a5; cursor:pointer;">Delete</button>`;
                    
                    let tierSelect = `
                        <select onchange="updateDealerTier('${d.id}', this.value)" style="padding:4px; font-size:12px; border-radius:4px; border:1px solid var(--border-color);">
                            <option value="default" ${d.tier === 'default' ? 'selected' : ''}>Default Wholesale</option>
                            <option value="tier1" ${d.tier === 'tier1' ? 'selected' : ''}>Distributor Tier 1</option>
                            <option value="tier2" ${d.tier === 'tier2' ? 'selected' : ''}>Distributor Tier 2</option>
                        </select>
                    `;
                    
                    tbody.innerHTML += `
                        <tr style="border-bottom:1px solid var(--border-color);">
                            <td style="padding:12px;">
                                <strong>${d.business_name}</strong><br>
                                <span style="font-size:11px; color:var(--text-muted);">GST: ${d.gst_number || 'N/A'}</span>
                            </td>
                            <td style="padding:12px;">
                                ${d.dealer_name}<br>
                                <span style="font-size:12px; color:var(--text-muted);">${d.email} | ${d.mobile_number}</span>
                            </td>
                            <td style="padding:12px;">${d.city}, ${d.state} (${d.pincode})</td>
                            <td style="padding:12px; font-size:12px; color:var(--text-muted);">${d.created_at}</td>
                            <td style="padding:12px;">${statusBadge}</td>
                            <td style="padding:12px;">${tierSelect}</td>
                            <td style="padding:12px; text-align:right;">${actions}</td>
                        </tr>
                    `;
                });
            })
            .catch(err => {
                console.error("Error loading dealers:", err);
                tbody.innerHTML = '<tr><td colspan="7" style="padding:20px; text-align:center; color:#dc2626;">Error loading dealer profiles.</td></tr>';
            });
    };
    
    window.updateDealerStatus = function(id, status) {
        fetch('/api/admin/dealers', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, status: status })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Dealer status updated: ' + status);
                loadDealers();
            } else {
                showAlert('error', data.message);
            }
        });
    };
    
    window.updateDealerTier = function(id, tier) {
        fetch('/api/admin/dealers', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, tier: tier })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Pricing tier updated to ' + tier);
            } else {
                showAlert('error', data.message);
            }
        });
    };
    
    window.deleteDealer = function(id) {
        if (!confirm("Are you sure you want to delete this dealer registration profile?")) return;
        
        fetch(`/api/admin/dealers?id=${id}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Dealer deleted successfully.');
                loadDealers();
            } else {
                showAlert('error', data.message);
            }
        });
    };
    
    window.loadActivityLogs = function() {
        const tbody = document.getElementById('activitiesTableBody');
        if (!tbody) return;
        
        fetch('/api/admin/dealer-activities')
            .then(res => res.json())
            .then(data => {
                localActivityLogs = data;
                renderLogs(data);
            })
            .catch(err => {
                console.error("Error fetching logs:", err);
                tbody.innerHTML = '<tr><td colspan="6" style="padding:20px; text-align:center; color:#dc2626;">Error loading logs.</td></tr>';
            });
    };
    
    function renderLogs(logs) {
        const tbody = document.getElementById('activitiesTableBody');
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding:20px; text-align:center; color:var(--text-muted);">No activity logs matched filters.</td></tr>';
            return;
        }
        
        logs.forEach(log => {
            let labelBg = '#f1f5f9';
            let labelColor = '#334155';
            if (log.action === 'login' || log.action === 'order_placed') {
                labelBg = '#dcfce7';
                labelColor = '#15803d';
            } else if (log.action === 'logout') {
                labelBg = '#fee2e2';
                labelColor = '#b91c1c';
            }
            
            let actionBadge = `<span style="background:${labelBg}; color:${labelColor}; font-size:11px; font-weight:700; padding:2px 6px; border-radius:4px; text-transform:uppercase;">${log.action}</span>`;
            
            tbody.innerHTML += `
                <tr style="border-bottom:1px solid var(--border-color); color:#4b5563;">
                    <td style="padding:10px; color:#9ca3af;">${log.created_at}</td>
                    <td style="padding:10px; font-weight:600; color:#111827;">${log.dealer_name}</td>
                    <td style="padding:10px; font-size:12px;">${log.business_name}</td>
                    <td style="padding:10px;">${actionBadge}</td>
                    <td style="padding:10px;">${log.details || ''}</td>
                    <td style="padding:10px; font-size:11px; color:#9ca3af;">
                        ${log.device} | ${log.ip_address}<br>
                        <span style="font-size:10px;">${log.browser}</span>
                    </td>
                </tr>
            `;
        });
    }
    
    window.filterLogs = function() {
        const q = document.getElementById('logSearchInput').value.trim().toLowerCase();
        const action = document.getElementById('logActionFilter').value;
        
        let filtered = localActivityLogs.filter(log => {
            let match = true;
            if (action && log.action !== action) match = false;
            if (q) {
                let name = (log.dealer_name || '').toLowerCase();
                let biz = (log.business_name || '').toLowerCase();
                let details = (log.details || '').toLowerCase();
                if (!name.includes(q) && !biz.includes(q) && !details.includes(q)) match = false;
            }
            return match;
        });
        
        renderLogs(filtered);
    };
    
    window.exportDealerLogs = function() {
        if (localActivityLogs.length === 0) {
            alert('No logs available to export.');
            return;
        }
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Timestamp,Dealer,Business,Action,Details,Device,IP,Browser\n";
        
        localActivityLogs.forEach(log => {
            let row = [
                log.created_at,
                `"${log.dealer_name.replace(/"/g, '""')}"`,
                `"${log.business_name.replace(/"/g, '""')}"`,
                log.action,
                `"${(log.details || '').replace(/"/g, '""')}"`,
                log.device,
                log.ip_address,
                `"${(log.browser || '').replace(/"/g, '""')}"`
            ].join(",");
            csvContent += row + "\n";
        });
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `b2b_dealer_activities_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
    
    window.loadDealerOrders = function() {
        const tbody = document.getElementById('dealerOrdersTableBody');
        if (!tbody) return;
        
        fetch('/api/admin/dealer-orders')
            .then(res => res.json())
            .then(data => {
                tbody.innerHTML = '';
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="padding:20px; text-align:center; color:var(--text-muted);">No B2B orders found.</td></tr>';
                    return;
                }
                
                data.forEach(o => {
                    let prodList = o.products.map(p => `${p.name} (x${p.quantity})`).join('<br>');
                    
                    let payBg = o.payment_status === 'paid' ? '#dcfce7' : '#fee2e2';
                    let payColor = o.payment_status === 'paid' ? '#15803d' : '#b91c1c';
                    let payBadge = `<span style="background:${payBg}; color:${payColor}; font-size:11px; font-weight:700; padding:2px 6px; border-radius:4px; text-transform:uppercase;">${o.payment_status}</span>`;
                    
                    let statusBg = '#f1f5f9';
                    let statusColor = '#334155';
                    if (o.order_status === 'delivered') { statusBg = '#dcfce7'; statusColor = '#15803d'; }
                    if (o.order_status === 'cancelled') { statusBg = '#fee2e2'; statusColor = '#b91c1c'; }
                    let statusBadge = `<span style="background:${statusBg}; color:${statusColor}; font-size:11px; font-weight:700; padding:2px 6px; border-radius:4px; text-transform:uppercase;">${o.order_status}</span>`;
                    
                    tbody.innerHTML += `
                        <tr style="border-bottom:1px solid var(--border-color);">
                            <td style="padding:12px;">
                                <strong>#${o.id.slice(0,8).toUpperCase()}</strong><br>
                                <span style="font-size:11px; color:var(--text-muted);">${o.created_at}</span>
                            </td>
                            <td style="padding:12px;">
                                <strong>${o.business_name}</strong><br>
                                <span style="font-size:12px; color:var(--text-muted);">${o.dealer_name} | ${o.mobile_number}</span>
                            </td>
                            <td style="padding:12px; font-size:12px; line-height:1.4;">${prodList}</td>
                            <td style="padding:12px; font-weight:700; color:#111827;">₹${o.total_value.toLocaleString()}</td>
                            <td style="padding:12px;">${payBadge}</td>
                            <td style="padding:12px;">${statusBadge}</td>
                            <td style="padding:12px; text-align:right;">
                                <select onchange="updateDealerOrderStatus('${o.id}', 'order_status', this.value)" style="padding:4px; font-size:12px; border-radius:4px; border:1px solid var(--border-color); margin-right:5px; cursor:pointer;">
                                    <option value="Initiated" ${o.order_status === 'Initiated' ? 'selected' : ''}>Initiated</option>
                                    <option value="Pending" ${o.order_status === 'Pending' ? 'selected' : ''}>Pending</option>
                                    <option value="Confirmed" ${o.order_status === 'Confirmed' ? 'selected' : ''}>Confirmed</option>
                                    <option value="Processing" ${o.order_status === 'Processing' ? 'selected' : ''}>Processing</option>
                                    <option value="Shipped" ${o.order_status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                                    <option value="Delivered" ${o.order_status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                                    <option value="Cancelled" ${o.order_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                                    <option value="Completed" ${o.order_status === 'Completed' ? 'selected' : ''}>Completed</option>
                                </select>
                                <select onchange="updateDealerOrderStatus('${o.id}', 'payment_status', this.value)" style="padding:4px; font-size:12px; border-radius:4px; border:1px solid var(--border-color); cursor:pointer;">
                                    <option value="unpaid" ${o.payment_status === 'unpaid' ? 'selected' : ''}>Unpaid</option>
                                    <option value="paid" ${o.payment_status === 'paid' ? 'selected' : ''}>Paid</option>
                                </select>
                            </td>
                        </tr>
                    `;
                });
            })
            .catch(err => {
                console.error("Error loading B2B orders:", err);
                tbody.innerHTML = '<tr><td colspan="7" style="padding:20px; text-align:center; color:#dc2626;">Error loading B2B orders.</td></tr>';
            });
    };
    
    window.updateDealerOrderStatus = function(id, field, value) {
        let payload = { id: id };
        payload[field] = value;
        
        fetch('/api/admin/dealer-orders', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Wholesale order updated.');
                loadDealerOrders();
            } else {
                showAlert('error', data.message);
            }
        });
    };

    // 20. Customer B2C Orders Operations
    window.loadCustomerOrders = function() {
        const tbody = document.getElementById("adminOrdersTableBody");
        if (!tbody) return;
        
        fetch('/api/admin/orders')
            .then(res => res.json())
            .then(orders => {
                tbody.innerHTML = "";
                if (orders.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--text-muted);">No customer orders found.</td></tr>`;
                    return;
                }
                
                orders.forEach(order => {
                    // Compile items
                    let itemsHtml = "";
                    if (order.items && order.items.length > 0) {
                        order.items.forEach(item => {
                            const imgUrl = item.product_image || '/static/uploads/prod_generic_1.webp';
                            itemsHtml += `<div style="margin-bottom: 8px; line-height: 1.4; display: flex; align-items: center; gap: 8px;">
                                <img src="${imgUrl}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid #e2e8f0;" onerror="this.src='/static/uploads/prod_generic_1.webp'">
                                <div>
                                    <strong>${item.product_name}</strong> x ${item.quantity} ${item.variant ? ' (' + item.variant + ')' : ''}<br>
                                    <span style="font-size: 11px; color: var(--text-muted);">Price: ₹${item.unit_price.toLocaleString('en-IN')} | SKU: ${item.sku}</span>
                                </div>
                            </div>`;
                        });
                    } else {
                        itemsHtml = `<span style="color: var(--text-muted);">No items</span>`;
                    }
                    
                    // Create status select options
                    const statuses = ["Initiated", "Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled", "Completed"];
                    let optionsHtml = "";
                    statuses.forEach(status => {
                        optionsHtml += `<option value="${status}" ${order.order_status === status ? 'selected' : ''}>${status}</option>`;
                    });
                    
                    const tr = document.createElement("tr");
                    tr.style.borderBottom = "1px solid var(--border-color)";
                    tr.className = "customer-order-row";
                    tr.dataset.orderId = order.order_id;
                    tr.dataset.customerName = order.customer_name;
                    tr.dataset.mobile = order.mobile_number;
                    tr.dataset.status = order.order_status;
                    
                    tr.innerHTML = `
                        <td style="padding: 12px 8px; font-weight: 700; font-family: monospace;">${order.order_id}</td>
                        <td style="padding: 12px 8px; color: var(--text-muted); font-size: 12px;">${order.created_at}</td>
                        <td style="padding: 12px 8px; line-height: 1.4;">
                            <strong>${order.customer_name}</strong><br>
                            Phone: ${order.mobile_number}<br>
                            ${order.email ? 'Email: ' + order.email : ''}
                        </td>
                        <td style="padding: 12px 8px; line-height: 1.4; max-width: 200px;">
                            ${order.delivery_address}<br>
                            <strong>PIN: ${order.pincode}</strong>
                            ${order.order_notes ? '<br><span style="font-size: 12px; color: #b45309; background: #fffbeb; padding: 2px 4px; border-radius: 4px;">Notes: ' + order.order_notes + '</span>' : ''}
                        </td>
                        <td style="padding: 12px 8px;">${itemsHtml}</td>
                        <td style="padding: 12px 8px; font-weight: 700;">₹${order.total_value.toLocaleString('en-IN')}</td>
                        <td style="padding: 12px 8px;">
                            <div style="display: flex; flex-direction: column; gap: 8px;">
                                <div>
                                    <span style="font-size: 10px; text-transform: uppercase; color: var(--text-muted); display: block; font-weight: 600; margin-bottom: 2px;">Order Status</span>
                                    <select onchange="updateCustomerOrderStatus('${order.order_id}', this.value)" style="padding: 4px 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; font-weight: 600; width: 100%;">
                                        ${optionsHtml}
                                    </select>
                                </div>
                                <div>
                                    <span style="font-size: 10px; text-transform: uppercase; color: var(--text-muted); display: block; font-weight: 600; margin-bottom: 2px;">Payment Status</span>
                                    <select onchange="updateCustomerOrderPaymentStatus('${order.order_id}', this.value)" style="padding: 4px 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; font-weight: 600; width: 100%;">
                                        <option value="Pending" ${order.payment_status === 'Pending' ? 'selected' : ''}>Pending</option>
                                        <option value="Paid" ${order.payment_status === 'Paid' ? 'selected' : ''}>Paid</option>
                                        <option value="Failed" ${order.payment_status === 'Failed' ? 'selected' : ''}>Failed</option>
                                        <option value="Refunded" ${order.payment_status === 'Refunded' ? 'selected' : ''}>Refunded</option>
                                    </select>
                                </div>
                            </div>
                        </td>
                        <td style="padding: 12px 8px; text-align: center;">
                            <button onclick="deleteCustomerOrder('${order.order_id}')" class="btn btn-danger btn-sm" style="background: #ef4444; border: none; color: white; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; display: inline-flex; align-items: center; gap: 4px;">
                                <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i> Delete
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            })
            .catch(err => {
                console.error("Error loading customer orders:", err);
                tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: #ef4444;">Failed to load orders.</td></tr>`;
            });
    };

    window.updateCustomerOrderStatus = function(orderId, status) {
        fetch('/api/admin/orders', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, order_status: status })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Order status updated.');
                loadCustomerOrders();
            } else {
                showAlert('error', data.message);
            }
        })
        .catch(err => {
            console.error("Failed to update order status:", err);
            showAlert('error', 'Status update failed.');
        });
    };

    window.updateCustomerOrderPaymentStatus = function(orderId, paymentStatus) {
        fetch('/api/admin/orders', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, payment_status: paymentStatus })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Payment status updated.');
                loadCustomerOrders();
            } else {
                showAlert('error', data.message);
            }
        })
        .catch(err => {
            console.error("Failed to update payment status:", err);
            showAlert('error', 'Payment status update failed.');
        });
    };

    window.deleteCustomerOrder = function(orderId) {
        if (!confirm("Are you sure you want to delete order " + orderId + "?")) return;
        
        fetch(`/api/admin/orders?id=${orderId}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Order deleted.');
                loadCustomerOrders();
            } else {
                showAlert('error', data.message);
            }
        })
        .catch(err => {
            console.error("Failed to delete order:", err);
            showAlert('error', 'Deletion failed.');
        });
    };

    window.filterOrdersTable = function() {
        const query = document.getElementById("adminOrderSearch").value.toLowerCase().trim();
        const statusFilter = document.getElementById("adminOrderStatusFilter").value;
        const rows = document.querySelectorAll(".customer-order-row");
        
        rows.forEach(row => {
            const oId = (row.dataset.orderId || "").toLowerCase();
            const name = (row.dataset.customerName || "").toLowerCase();
            const mobile = (row.dataset.mobile || "").toLowerCase();
            const status = row.dataset.status || "";
            
            const matchesQuery = oId.includes(query) || name.includes(query) || mobile.includes(query);
            const matchesStatus = !statusFilter || status === statusFilter;
            
            if (matchesQuery && matchesStatus) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    };

    // 19. Quick Dealer Prices Modal & Operations
    const dealerPricesModal = document.getElementById('dealerPricesModal');
    
    window.editDealerPrices = function(id) {
        fetch(`/api/admin/products?id=${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.id) {
                    document.getElementById('dealerPricesForm').reset();
                    document.getElementById('dpFormProdId').value = data.id;
                    document.getElementById('dpFormProdName').innerText = data.name;
                    
                    const dp = data.dealer_prices || {};
                    document.getElementById('dpDefaultPrice').value = dp.default !== null && dp.default !== undefined ? dp.default : (data.wholesale_price || 0.0);
                    document.getElementById('dpSilverPrice').value = dp.silver !== null && dp.silver !== undefined ? dp.silver : '';
                    document.getElementById('dpGoldPrice').value = dp.gold !== null && dp.gold !== undefined ? dp.gold : '';
                    document.getElementById('dpPlatinumPrice').value = dp.platinum !== null && dp.platinum !== undefined ? dp.platinum : '';
                    
                    dealerPricesModal.classList.add('active');
                }
            })
            .catch(err => {
                console.error("Error loading product dealer prices:", err);
                showAlert('error', 'Failed to retrieve product details.');
            });
    };
    
    window.closeDealerPricesModal = function() {
        dealerPricesModal.classList.remove('active');
    };
    
    const dealerPricesForm = document.getElementById('dealerPricesForm');
    if (dealerPricesForm) {
        dealerPricesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const pId = document.getElementById('dpFormProdId').value;
            
            // First fetch the existing product data to make sure we don't drop other fields during partial updates
            fetch(`/api/admin/products?id=${pId}`)
                .then(res => res.json())
                .then(product => {
                    if (!product.id) {
                        showAlert('error', 'Product not found.');
                        return;
                    }
                    
                    // Override only dealer prices
                    product.dealer_prices = {
                        default: parseFloat(document.getElementById('dpDefaultPrice').value) || 0.0,
                        silver: document.getElementById('dpSilverPrice').value.trim() !== '' ? parseFloat(document.getElementById('dpSilverPrice').value) : null,
                        gold: document.getElementById('dpGoldPrice').value.trim() !== '' ? parseFloat(document.getElementById('dpGoldPrice').value) : null,
                        platinum: document.getElementById('dpPlatinumPrice').value.trim() !== '' ? parseFloat(document.getElementById('dpPlatinumPrice').value) : null
                    };
                    // Ensure wholesale_price field matches default
                    product.wholesale_price = product.dealer_prices.default;
                    
                    // Save back
                    return fetch('/api/admin/products', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(product)
                    });
                })
                .then(res => res.json())
                .then(data => {
                    if (data && data.success) {
                        closeDealerPricesModal();
                        window.location.reload();
                    } else if (data) {
                        showAlert('error', data.message);
                    }
                })
                .catch(err => {
                    console.error("Error saving B2B prices:", err);
                    showAlert('error', 'Failed to save updated dealer prices.');
                });
        });
    };

    window.loadProductsAndRedrawTable = function() {
        const tbody = document.getElementById('adminProductsTableBody');
        if (!tbody) return;

        // Show a brief loading indicator / opacity change
        tbody.style.opacity = '0.5';

        fetch('/api/admin/products')
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch products from database.");
                return res.json();
            })
            .then(products => {
                tbody.innerHTML = '';
                products.forEach(p => {
                    const tr = document.createElement('tr');
                    
                    // Format main prices
                    let priceHtml = '';
                    if (p.offer_price) {
                        priceHtml = `<span style="color:var(--accent-color); font-weight:700;">₹${Number(p.offer_price).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
                                     <span style="text-decoration:line-through; font-size:11px; color:var(--text-muted); margin-left:4px;">₹${Number(p.price).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>`;
                    } else {
                        priceHtml = `₹${Number(p.price).toLocaleString('en-IN', {maximumFractionDigits:0})}`;
                    }

                    // Format B2B/Wholesale prices
                    const dp = p.dealer_prices || {};
                    const defaultWholesale = dp.default || p.wholesale_price || 0;
                    let wholesaleHtml = `<span style="color:#854d0e; font-weight:700;">₹${Number(defaultWholesale).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>`;
                    
                    if (dp.silver || dp.gold || dp.platinum) {
                        wholesaleHtml += `<div style="font-size:10px; color:var(--text-muted); margin-top:2px; display:flex; gap:5px; flex-wrap:wrap;">`;
                        if (dp.silver) {
                            wholesaleHtml += `<span style="background:#f1f5f9; padding:1px 3px; border-radius:2px;" title="Silver Tier">S: ₹${Number(dp.silver).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>`;
                        }
                        if (dp.gold) {
                            wholesaleHtml += `<span style="background:#fef3c7; color:#d97706; padding:1px 3px; border-radius:2px;" title="Gold Tier">G: ₹${Number(dp.gold).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>`;
                        }
                        if (dp.platinum) {
                            wholesaleHtml += `<span style="background:#ede9fe; color:#7c3aed; padding:1px 3px; border-radius:2px;" title="Platinum Tier">P: ₹${Number(dp.platinum).toLocaleString('en-IN', {maximumFractionDigits:0})}</span>`;
                        }
                        wholesaleHtml += `</div>`;
                    }

                    // Format Badges
                    let badgesHtml = '';
                    if (p.is_featured) {
                        badgesHtml += `<span class="admin-table-badge badge-featured" style="margin-right:4px;">Featured</span>`;
                    }
                    if (p.is_new_arrival) {
                        badgesHtml += `<span class="admin-table-badge badge-new" style="margin-right:4px;">New</span>`;
                    }
                    if (p.is_best_seller) {
                        badgesHtml += `<span class="admin-table-badge" style="background:#E67E22; color:white;">Hot</span>`;
                    }

                    // Format Status dot & Stock info
                    const statusClass = p.status === 'active' ? 'active' : 'inactive';
                    const statusText = p.status ? p.status.charAt(0).toUpperCase() + p.status.slice(1) : 'Inactive';
                    let stockHtml = '';
                    if (p.stock_status === 'out_of_stock') {
                        stockHtml = `<div style="font-size:11px; font-weight:700; color:#dc2626; margin-top:2px;">Out of Stock ${p.allow_preorder ? '(Pre-order)' : ''}</div>`;
                    } else {
                        stockHtml = `<div style="font-size:11px; color:#16a34a; margin-top:2px;">In Stock (${p.stock_quantity !== undefined && p.stock_quantity !== null ? p.stock_quantity : 10})</div>`;
                    }

                    tr.innerHTML = `
                        <td>${p.id}</td>
                        <td style="font-weight:700;">${p.name}</td>
                        <td>${p.category_name || 'Uncategorized'}</td>
                        <td>${p.sku || ''}</td>
                        <td>${priceHtml}</td>
                        <td>${wholesaleHtml}</td>
                        <td>${badgesHtml}</td>
                        <td>
                            <span class="status-dot ${statusClass}"></span> ${statusText}
                            ${stockHtml}
                        </td>
                        <td>
                            <div style="display:flex; gap:6px;">
                                <button class="btn-icon" onclick="editProduct('${p.id}')" title="Edit Product"><i data-lucide="edit-3"></i></button>
                                <button class="btn-icon" onclick="editDealerPrices('${p.id}')" title="Edit Dealer Prices" style="color:#854d0e;"><i data-lucide="coins"></i></button>
                                <button class="btn-icon" onclick="duplicateProduct('${p.id}')" title="Duplicate Product" style="color:var(--accent-color);"><i data-lucide="copy"></i></button>
                                <button class="btn-icon delete" onclick="deleteProduct('${p.id}')" title="Delete Product"><i data-lucide="trash-2"></i></button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            })
            .catch(err => {
                console.error("Error redrawing products table:", err);
                showAlert('error', 'Error refreshing catalog display.');
            })
            .finally(() => {
                tbody.style.opacity = '1';
            });
    };

    // 21. Stock Availability Notifications Operations
    window.loadStockNotifications = function() {
        const tbody = document.getElementById("stockNotificationsBody");
        if (!tbody) return;

        fetch('/api/admin/stock-notifications')
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    console.error("Failed to load stock notifications:", data.message);
                    return;
                }
                const notifs = data.notifications || [];
                tbody.innerHTML = "";
                if (notifs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No stock notification requests found.</td></tr>`;
                    return;
                }

                notifs.forEach(notif => {
                    const isEmail = notif.contact_info && notif.contact_info.includes('@');
                    const cleanPhone = notif.contact_info ? notif.contact_info.replace(/\D/g, '') : '';
                    const contactHtml = isEmail 
                        ? `<a href="mailto:${notif.contact_info}" style="color: var(--accent-color); font-weight: 700; text-decoration: underline; display: inline-flex; align-items: center; gap: 4px;"><i data-lucide="mail" style="width: 14px; height: 14px;"></i> ${notif.contact_info}</a>`
                        : `<a href="https://wa.me/${cleanPhone}?text=Hello,%20we%20are%20pleased%20to%20inform%20you%20that%20the%20product%20you%20inquired%20about%20is%20now%20back%20in%20stock!" target="_blank" style="color: #059669; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;"><i data-lucide="message-circle" style="width: 14px; height: 14px;"></i> ${notif.contact_info}</a>`;

                    const isNotified = notif.status === 'notified' || notif.status === 'resolved';
                    const statusBadge = `<span style="display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; background: ${isNotified ? '#ecfdf5' : '#fef3c7'}; color: ${isNotified ? '#065f46' : '#92400e'}; border: 1px solid ${isNotified ? '#a7f3d0' : '#fde68a'};">${notif.status || 'pending'}</span>`;

                    const markBtn = !isNotified 
                        ? `<button type="button" class="btn btn-sm" onclick="markNotificationStatus(${notif.id}, 'notified')" style="padding: 4px 8px; font-size: 11px; font-weight: 700; background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; border-radius: 4px; cursor: pointer;" title="Mark as Notified">Mark Notified</button>`
                        : '';

                    const tr = document.createElement("tr");
                    tr.style.borderBottom = "1px solid var(--border-color)";
                    tr.id = `notifRow_${notif.id}`;
                    tr.innerHTML = `
                        <td style="padding: 12px 10px; font-weight: 700; color: var(--text-muted);">#${notif.id}</td>
                        <td style="padding: 12px 10px;">
                            <div style="font-weight: 700; color: var(--text-dark); margin-bottom: 2px;">${notif.product_name}</div>
                            <span style="font-size: 12px; color: var(--text-muted);">Product ID: ${notif.product_id}</span>
                        </td>
                        <td style="padding: 12px 10px;">${contactHtml}</td>
                        <td style="padding: 12px 10px; font-size: 13px; color: var(--text-muted);">${notif.formatted_date || notif.created_at || 'N/A'}</td>
                        <td style="padding: 12px 10px; text-align: center;">${statusBadge}</td>
                        <td style="padding: 12px 10px; text-align: right;">
                            <div style="display: inline-flex; gap: 6px; justify-content: flex-end;">
                                ${markBtn}
                                <button type="button" class="btn btn-sm" onclick="deleteStockNotification(${notif.id})" style="padding: 4px 8px; font-size: 11px; font-weight: 700; background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; border-radius: 4px; cursor: pointer;" title="Delete">
                                    <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                if (typeof lucide !== 'undefined') lucide.createIcons();
            })
            .catch(err => {
                console.error("Error loading stock notifications:", err);
            });
    };

    window.markNotificationStatus = function(notifId, status) {
        fetch(`/api/admin/stock-notifications/${notifId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Notification updated.');
                loadStockNotifications();
            } else {
                showAlert('error', data.message || 'Failed to update notification.');
            }
        })
        .catch(err => {
            console.error("Error updating notification status:", err);
            showAlert('error', 'Server error updating notification.');
        });
    };

    window.deleteStockNotification = function(notifId) {
        if (!confirm("Are you sure you want to delete this stock notification?")) return;
        fetch(`/api/admin/stock-notifications/${notifId}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || 'Notification deleted.');
                const row = document.getElementById(`notifRow_${notifId}`);
                if (row) row.remove();
            } else {
                showAlert('error', data.message || 'Failed to delete notification.');
            }
        })
        .catch(err => {
            console.error("Error deleting stock notification:", err);
            showAlert('error', 'Server error deleting notification.');
        });
    };

    // Document ready closing blocks
});
