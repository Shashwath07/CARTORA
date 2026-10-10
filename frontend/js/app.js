/* ================================================================
   CARTORA — Complete SPA Application
   ================================================================ */
const Cartora = (function () {
    'use strict';

    /* ── State ── */
    const state = {
        customer: null,
        cart: [],
        currentPage: '',
        conversations: [],          // { id, title, messages[], created }
        activeConversationId: null,
        orderContext: null,          // order_id for chat context
        lastDiag: null,              // { memories_used, memory_saved }
        chatHomeVisible: true
    };

    /* ================================================================
       API CLIENT
       ================================================================ */
    const api = {
        async request(url, opts = {}) {
            opts.credentials = 'same-origin';
            if (!opts.headers) opts.headers = {};
            if (opts.body && typeof opts.body === 'object') {
                opts.headers['Content-Type'] = 'application/json';
                opts.body = JSON.stringify(opts.body);
            }
            opts.headers['X-Requested-With'] = 'XMLHttpRequest';
            try {
                const res = await fetch(url, opts);
                if (res.status === 401) { window.location.href = '/'; return null; }
                const data = await res.json();
                if (!res.ok) {
                    const msg = data.error || 'Something went wrong';
                    ui.toast(msg, 'error');
                    return null;
                }
                return data;
            } catch (e) {
                ui.toast('Network error. Please check your connection.', 'error');
                return null;
            }
        },
        get(url) { return this.request(url); },
        post(url, body) { return this.request(url, { method: 'POST', body }); }
    };

    /* ================================================================
       UI UTILITIES
       ================================================================ */
    const ui = {
        toast(msg, type = 'info') {
            const c = document.getElementById('toasts');
            const icons = { success: '✓', error: '✕', info: 'ℹ' };
            const t = document.createElement('div');
            t.className = `toast toast-${type}`;
            t.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ'}</span><span>${this.esc(msg)}</span>`;
            c.appendChild(t);
            setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; setTimeout(() => t.remove(), 300); }, 4000);
        },
        esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
        formatPrice(n) { return '₹' + Number(n).toLocaleString('en-IN'); },
        formatDate(d) {
            if (!d) return '—';
            return new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
        },
        greeting() {
            const h = new Date().getHours();
            if (h < 5) return 'Good night';
            if (h < 12) return 'Good morning';
            if (h < 17) return 'Good afternoon';
            if (h < 21) return 'Good evening';
            return 'Good night';
        },
        timeNow() { return new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }); },
        badge(status) {
            if (!status) return '';
            const s = status.toLowerCase();
            let cls = 'badge-info';
            if (['delivered', 'completed', 'active', 'success', 'approved'].some(k => s.includes(k))) cls = 'badge-success';
            else if (['shipped', 'packed', 'processing', 'pending', 'requested', 'submitted', 'open'].some(k => s.includes(k))) cls = 'badge-warning';
            else if (['expired', 'failed', 'cancelled', 'denied', 'not eligible'].some(k => s.includes(k))) cls = 'badge-error';
            else if (['placed', 'order placed'].some(k => s.includes(k))) cls = 'badge-info';
            return `<span class="badge ${cls}">${this.esc(status)}</span>`;
        },
        loading(container) {
            container.innerHTML = `<div class="content-inner"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line-sm"></div></div>`;
        },
        empty(icon, title, desc, actionText, actionHash) {
            let action = actionText ? `<a href="#${actionHash || 'shop'}" class="btn btn-primary">${this.esc(actionText)}</a>` : '';
            return `<div class="empty-state"><div class="empty-icon">${icon}</div><div class="empty-title">${this.esc(title)}</div><div class="empty-desc">${this.esc(desc)}</div>${action}</div>`;
        }
    };

    /* ================================================================
       ROUTER
       ================================================================ */
    const router = {
        init() {
            window.addEventListener('hashchange', () => this.route());
            this.route();
        },
        route() {
            const hash = (window.location.hash || '#home').slice(1);
            const parts = hash.split('/');
            const page = parts[0] || 'home';
            const param = parts.slice(1).join('/');
            state.currentPage = page;
            this.renderShell();
            const content = document.getElementById('content');
            content.innerHTML = '<div class="content-inner" id="page"></div>';
            const p = document.getElementById('page');
            ui.loading(p);
            const map = {
                home: () => pages.home(p),
                shop: () => pages.shop(p),
                product: () => pages.productDetail(p, param),
                cart: () => pages.cart(p),
                orders: () => pages.orders(p),
                order: () => pages.orderDetail(p, param),
                delivery: () => pages.delivery(p, param),
                returns: () => pages.returns(p),
                'return': () => pages.returnForm(p, param),
                warranty: () => pages.warranty(p),
                'warranty-claim': () => pages.warrantyClaim(p, param),
                assist: () => pages.assist(content),
                cases: () => pages.cases(p),
                account: () => pages.account(p)
            };
            (map[page] || (() => { p.innerHTML = ui.empty('🔍', 'Page not found', 'The page you are looking for does not exist.', 'Go Home', 'home'); }))();
        },
        renderShell() {
            const sb = document.getElementById('sidebar');
            const nav = [
                { id: 'home', icon: '🏠', label: 'Home' },
                { id: 'shop', icon: '🛍️', label: 'Shop' },
                { id: 'orders', icon: '📦', label: 'My Orders' },
                { id: 'delivery', icon: '🚚', label: 'Delivery' },
                { id: 'returns', icon: '↩️', label: 'Returns & Refunds' },
                { id: 'warranty', icon: '🛡️', label: 'Warranty & Repairs' },
                { id: 'assist', icon: '💬', label: 'Cartora Assist' },
                { id: 'cases', icon: '📋', label: 'My Cases' },
                { id: 'account', icon: '👤', label: 'Account' }
            ];
            const cartCount = state.cart.length;
            sb.innerHTML = `
                <div class="sidebar-brand">
                    <div class="sidebar-brand-icon">C</div>
                    <div>
                        <div class="sidebar-brand-text">Cartora</div>
                        <div class="sidebar-brand-sub">E-Commerce</div>
                    </div>
                </div>
                <div class="sidebar-nav">
                    <div class="nav-section-label">Navigation</div>
                    ${nav.map(n => {
                        const active = state.currentPage === n.id ? 'active' : '';
                        const badge = n.id === 'cart' && cartCount ? `<span class="nav-badge">${cartCount}</span>` : '';
                        return `<a href="#${n.id}" class="nav-item ${active}"><span class="nav-icon">${n.icon}</span>${n.label}${badge}</a>`;
                    }).join('')}
                    ${cartCount > 0 ? `<a href="#cart" class="nav-item ${state.currentPage === 'cart' ? 'active' : ''}"><span class="nav-icon">🛒</span>Cart<span class="nav-badge">${cartCount}</span></a>` : ''}
                </div>
            `;
            const tb = document.getElementById('topbar');
            const pageNames = { home: 'Home', shop: 'Shop', orders: 'My Orders', order: 'Order Detail', product: 'Product', cart: 'Cart', delivery: 'Delivery', returns: 'Returns & Refunds', 'return': 'Start Return', warranty: 'Warranty & Repairs', 'warranty-claim': 'Warranty Claim', assist: 'Cartora Assist', cases: 'My Cases', account: 'Account' };
            const pageName = pageNames[state.currentPage] || state.currentPage;
            tb.innerHTML = `
                <div class="breadcrumb">Cartora<span class="breadcrumb-sep">/</span><span class="breadcrumb-page">${pageName}</span></div>
                <div class="user-info">
                    <div class="avatar">${state.customer.avatar_initials || 'U'}</div>
                    <div>
                        <div class="user-name">${ui.esc(state.customer.name)}</div>
                        <div class="user-tier">${ui.esc(state.customer.tier)}</div>
                    </div>
                    <button class="btn-logout" id="btnLogout">Logout</button>
                </div>
            `;
            document.getElementById('btnLogout').onclick = async () => {
                await api.post('/api/logout');
                window.location.href = '/';
            };
        }
    };

    /* ================================================================
       PAGES
       ================================================================ */
    const pages = {
        /* ── HOME ── */
        async home(el) {
            const ordersData = await api.get('/api/orders');
            const orders = ordersData ? ordersData.orders || [] : [];
            el.innerHTML = `
                <h1 class="page-title">${ui.greeting()}, ${ui.esc(state.customer.name.split(' ')[0])}.</h1>
                <p class="page-subtitle">Here's what's happening with your Cartora account.</p>
                <div class="quick-actions mb-xl">
                    <a href="#orders" class="quick-action"><span class="quick-action-icon">📦</span>Track Orders</a>
                    <a href="#returns" class="quick-action"><span class="quick-action-icon">↩️</span>Start Return</a>
                    <a href="#warranty" class="quick-action"><span class="quick-action-icon">🛡️</span>Check Warranty</a>
                    <a href="#assist" class="quick-action"><span class="quick-action-icon">💬</span>Ask Cartora Assist</a>
                </div>
                <h2>Recent Orders</h2>
                ${orders.length > 0 ? `<div class="grid gap-md">${orders.map(o => `
                    <a href="#order/${o.order_id}" class="order-card">
                        <div class="order-emoji">${o.image_placeholder || '📦'}</div>
                        <div class="order-details">
                            <div class="order-product-name">${ui.esc(o.product_name)}</div>
                            <div class="order-meta">${o.order_id} · ${ui.formatDate(o.ordered_date)} · ${ui.badge(o.status)}</div>
                        </div>
                        <div class="order-price">${ui.formatPrice(o.price)}</div>
                    </a>
                `).join('')}</div>` : ui.empty('📦', 'No orders yet', 'Start shopping to see your orders here.', 'Browse Shop', 'shop')}
                <h2 class="mt-xl">Recommended for You</h2>
                <div class="grid grid-auto-4" id="homeProducts"></div>
            `;
            const pd = await api.get('/api/products');
            const prods = pd ? (pd.products || []).slice(0, 4) : [];
            document.getElementById('homeProducts').innerHTML = prods.map(p => `
                <a href="#product/${p.id}" class="product-card">
                    <div class="product-emoji">${p.image_placeholder}</div>
                    <div class="product-name">${ui.esc(p.name)}</div>
                    <div class="product-price">${ui.formatPrice(p.price)}</div>
                </a>
            `).join('');
        },

        /* ── SHOP ── */
        async shop(el) {
            const data = await api.get('/api/products');
            if (!data) return;
            const products = data.products || [];
            const cats = ['All', ...(data.categories || [])];
            let activeFilter = 'All';
            const render = (filter) => {
                activeFilter = filter;
                const filtered = filter === 'All' ? products : products.filter(p => p.category === filter);
                document.getElementById('shopGrid').innerHTML = filtered.map(p => `
                    <a href="#product/${p.id}" class="product-card">
                        <div class="product-emoji">${p.image_placeholder}</div>
                        <div class="product-name">${ui.esc(p.name)}</div>
                        <div class="product-price">${ui.formatPrice(p.price)}</div>
                        <div class="product-meta">
                            <span class="product-rating">★ ${p.rating}</span>
                            <span>${p.reviews} reviews</span>
                        </div>
                        <div class="product-add-btn"><button class="btn btn-secondary btn-sm w-full add-cart-btn" data-id="${p.id}">Add to Cart</button></div>
                    </a>
                `).join('');
                document.querySelectorAll('.filter-pill').forEach(fp => fp.classList.toggle('active', fp.dataset.cat === filter));
                document.querySelectorAll('.add-cart-btn').forEach(btn => {
                    btn.onclick = (e) => {
                        e.preventDefault(); e.stopPropagation();
                        const prod = products.find(pp => pp.id === btn.dataset.id);
                        if (prod) { state.cart.push(prod); ui.toast(`${prod.name} added to cart`, 'success'); router.renderShell(); }
                    };
                });
            };
            el.innerHTML = `
                <h1 class="page-title">Shop</h1>
                <p class="page-subtitle">Browse our curated selection of quality products.</p>
                <div class="search-bar">
                    <input type="text" class="search-input" id="shopSearch" placeholder="Search products...">
                </div>
                <div class="filter-pills" id="shopFilters">
                    ${cats.map(c => `<button class="filter-pill ${c === 'All' ? 'active' : ''}" data-cat="${c}">${c}</button>`).join('')}
                </div>
                <div class="grid grid-auto-4" id="shopGrid"></div>
            `;
            render('All');
            document.querySelectorAll('.filter-pill').forEach(fp => { fp.onclick = () => render(fp.dataset.cat); });
            document.getElementById('shopSearch').oninput = (e) => {
                const q = e.target.value.toLowerCase();
                const filtered = products.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q) || p.description.toLowerCase().includes(q));
                document.getElementById('shopGrid').innerHTML = filtered.map(p => `
                    <a href="#product/${p.id}" class="product-card">
                        <div class="product-emoji">${p.image_placeholder}</div>
                        <div class="product-name">${ui.esc(p.name)}</div>
                        <div class="product-price">${ui.formatPrice(p.price)}</div>
                        <div class="product-meta"><span class="product-rating">★ ${p.rating}</span><span>${p.reviews} reviews</span></div>
                        <div class="product-add-btn"><button class="btn btn-secondary btn-sm w-full add-cart-btn" data-id="${p.id}">Add to Cart</button></div>
                    </a>
                `).join('');
                document.querySelectorAll('.add-cart-btn').forEach(btn => {
                    btn.onclick = (ev) => {
                        ev.preventDefault(); ev.stopPropagation();
                        const prod = products.find(pp => pp.id === btn.dataset.id);
                        if (prod) { state.cart.push(prod); ui.toast(`${prod.name} added to cart`, 'success'); router.renderShell(); }
                    };
                });
            };
        },

        /* ── PRODUCT DETAIL ── */
        async productDetail(el, id) {
            const data = await api.get(`/api/products/${id}`);
            if (!data || !data.product) return el.innerHTML = ui.empty('🔍', 'Product not found', 'This product does not exist.');
            const p = data.product;
            el.innerHTML = `
                <a href="#shop" class="back-link">← Back to Shop</a>
                <div class="card">
                    <div class="flex gap-xl" style="flex-wrap:wrap;">
                        <div style="flex:1; min-width:200px; text-align:center; padding:40px 0;">
                            <div style="font-size:120px; line-height:1;">${p.image_placeholder}</div>
                        </div>
                        <div style="flex:2; min-width:300px;">
                            <div class="flex items-center gap-md mb-sm">
                                <span class="badge badge-info">${ui.esc(p.category)}</span>
                                ${p.in_stock ? '<span class="badge badge-success">In Stock</span>' : '<span class="badge badge-error">Out of Stock</span>'}
                            </div>
                            <h1 style="margin-bottom:8px;">${ui.esc(p.name)}</h1>
                            <div class="product-price" style="font-size:28px; margin-bottom:16px;">${ui.formatPrice(p.price)}</div>
                            <div class="product-meta" style="justify-content:flex-start; margin-bottom:20px;">
                                <span class="product-rating">★ ${p.rating}</span>
                                <span>${p.reviews} reviews</span>
                            </div>
                            <p>${ui.esc(p.description)}</p>
                            <hr class="divider">
                            <h3>Specifications</h3>
                            <ul style="list-style:none; padding:0;">
                                ${p.specs.map(s => `<li style="padding:4px 0; color:var(--text-secondary); font-size:14px;">• ${ui.esc(s)}</li>`).join('')}
                            </ul>
                            <hr class="divider">
                            <div class="flex gap-lg mb-md">
                                <div><span class="text-xs text-muted">Delivery</span><br><strong>${p.delivery_estimate_days} days</strong></div>
                                <div><span class="text-xs text-muted">Returns</span><br><strong>${p.return_window_days} day window</strong></div>
                                <div><span class="text-xs text-muted">Warranty</span><br><strong>${p.warranty_months ? p.warranty_months + ' months' : 'No warranty'}</strong></div>
                            </div>
                            <button class="btn btn-primary btn-lg" id="btnAddCart">Add to Cart</button>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('btnAddCart').onclick = () => {
                state.cart.push(p);
                ui.toast(`${p.name} added to cart`, 'success');
                router.renderShell();
            };
        },

        /* ── CART ── */
        async cart(el) {
            if (state.cart.length === 0) { el.innerHTML = ui.empty('🛒', 'Your cart is empty', 'Browse our shop to add products.', 'Browse Shop', 'shop'); return; }
            const total = state.cart.reduce((s, p) => s + p.price, 0);
            const renderCart = () => {
                el.innerHTML = `
                    <h1 class="page-title">Cart</h1>
                    <div class="card mb-lg">
                        ${state.cart.map((p, i) => `
                            <div class="flex items-center justify-between" style="padding:16px 0; border-bottom:1px solid var(--card-border);">
                                <div class="flex items-center gap-md">
                                    <span style="font-size:32px;">${p.image_placeholder}</span>
                                    <div>
                                        <div style="font-weight:600;">${ui.esc(p.name)}</div>
                                        <div class="text-sm text-muted">${ui.esc(p.category)}</div>
                                    </div>
                                </div>
                                <div class="flex items-center gap-lg">
                                    <span style="font-weight:700;">${ui.formatPrice(p.price)}</span>
                                    <button class="btn btn-ghost btn-sm remove-btn" data-idx="${i}">✕</button>
                                </div>
                            </div>
                        `).join('')}
                        <div class="flex justify-between items-center mt-lg" style="font-size:18px;">
                            <strong>Total</strong><strong>${ui.formatPrice(state.cart.reduce((s, p) => s + p.price, 0))}</strong>
                        </div>
                    </div>
                    <div class="card mb-lg">
                        <h3>Delivery Address</h3>
                        <p>${ui.esc(state.customer.saved_address || 'Address on file')}</p>
                        <h3 class="mt-md">Payment Method</h3>
                        <div class="flex gap-md mt-sm">
                            <label class="flex items-center gap-sm" style="cursor:pointer;"><input type="radio" name="pay" value="UPI - Demo" checked style="accent-color:var(--accent);"> UPI - Demo</label>
                            <label class="flex items-center gap-sm" style="cursor:pointer;"><input type="radio" name="pay" value="Card - Demo" style="accent-color:var(--accent);"> Card - Demo</label>
                        </div>
                    </div>
                    <button class="btn btn-primary btn-lg btn-block" id="btnCheckout">Place Demo Order</button>
                    <p class="text-xs text-muted text-center mt-sm">This is a prototype. No real payment will be processed.</p>
                `;
                document.querySelectorAll('.remove-btn').forEach(b => {
                    b.onclick = () => { state.cart.splice(parseInt(b.dataset.idx), 1); renderCart(); router.renderShell(); };
                });
                const checkoutBtn = document.getElementById('btnCheckout');
                if (checkoutBtn) {
                    checkoutBtn.onclick = async () => {
                        checkoutBtn.disabled = true;
                        checkoutBtn.textContent = 'Placing order...';
                        const payMethod = document.querySelector('input[name="pay"]:checked')?.value || 'UPI - Demo';
                        const item = state.cart[0];
                        const res = await api.post('/api/orders/demo-checkout', { product_id: item.id, payment_method: payMethod });
                        if (res) {
                            state.cart = [];
                            ui.toast('Order placed successfully!', 'success');
                            window.location.hash = `#order/${res.order.order_id}`;
                        } else { checkoutBtn.disabled = false; checkoutBtn.textContent = 'Place Demo Order'; }
                    };
                }
            };
            renderCart();
        },

        /* ── MY ORDERS ── */
        async orders(el) {
            const data = await api.get('/api/orders');
            if (!data) return;
            const orders = data.orders || [];
            if (orders.length === 0) { el.innerHTML = ui.empty('📦', 'No orders yet', 'Your orders will appear here after you make a purchase.', 'Browse Shop', 'shop'); return; }
            el.innerHTML = `
                <h1 class="page-title">My Orders</h1>
                <p class="page-subtitle">${orders.length} order${orders.length !== 1 ? 's' : ''}</p>
                <div class="grid gap-md">
                    ${orders.map(o => `
                        <a href="#order/${o.order_id}" class="order-card">
                            <div class="order-emoji">${o.image_placeholder || '📦'}</div>
                            <div class="order-details">
                                <div class="order-product-name">${ui.esc(o.product_name)}</div>
                                <div class="order-meta">${o.order_id} · Ordered ${ui.formatDate(o.ordered_date)}</div>
                                <div class="mt-sm">${ui.badge(o.status)}</div>
                            </div>
                            <div class="order-price">${ui.formatPrice(o.price)}</div>
                        </a>
                    `).join('')}
                </div>
            `;
        },

        /* ── ORDER DETAIL ── */
        async orderDetail(el, orderId) {
            const data = await api.get(`/api/orders/${orderId}`);
            if (!data || !data.order) { el.innerHTML = ui.empty('📦', 'Order not found', 'This order does not exist or does not belong to you.'); return; }
            const o = data.order;
            const steps = o.delivery_steps || [];
            const hasWarranty = o.warranty_months > 0;
            const isDelivered = o.status === 'Delivered';
            el.innerHTML = `
                <a href="#orders" class="back-link">← Back to Orders</a>
                <div class="card mb-lg">
                    <div class="order-header">
                        <div class="order-header-info">
                            <h1>${ui.esc(o.product_name)}</h1>
                            <div class="flex items-center gap-md mb-md">
                                ${ui.badge(o.status)}
                                <span class="text-sm text-muted">${o.order_id}</span>
                            </div>
                        </div>
                        <div class="order-header-emoji">${o.image_placeholder || '📦'}</div>
                    </div>
                    <div class="detail-grid">
                        <div class="detail-item"><div class="detail-label">Ordered</div><div class="detail-value">${ui.formatDate(o.ordered_date)}</div></div>
                        <div class="detail-item"><div class="detail-label">${isDelivered ? 'Delivered' : 'Expected'}</div><div class="detail-value">${ui.formatDate(o.delivered_date || o.expected_delivery)}</div></div>
                        <div class="detail-item"><div class="detail-label">Price</div><div class="detail-value">${ui.formatPrice(o.price)}</div></div>
                        <div class="detail-item"><div class="detail-label">Payment</div><div class="detail-value">${ui.esc(o.payment_method)}</div></div>
                        ${o.return_deadline ? `<div class="detail-item"><div class="detail-label">Return Deadline</div><div class="detail-value">${ui.formatDate(o.return_deadline)}</div></div>` : ''}
                        ${o.warranty_end ? `<div class="detail-item"><div class="detail-label">Warranty Until</div><div class="detail-value">${ui.formatDate(o.warranty_end)}</div></div>` : ''}
                        <div class="detail-item"><div class="detail-label">Courier</div><div class="detail-value">${ui.esc(o.courier || '—')}</div></div>
                        <div class="detail-item"><div class="detail-label">Tracking</div><div class="detail-value">${ui.esc(o.tracking_id || '—')}</div></div>
                    </div>
                    <div class="detail-item mb-lg"><div class="detail-label">Delivery Address</div><div class="detail-value">${ui.esc(o.delivery_address || '—')}</div></div>
                </div>
                <div class="card mb-lg">
                    <h3>Delivery Timeline</h3>
                    <div class="timeline">
                        ${steps.map((s, i) => {
                            const completed = s.completed;
                            const isCurrent = !completed && (i === 0 || steps[i - 1].completed);
                            return `<div class="timeline-item ${completed ? 'completed' : ''} ${isCurrent ? 'current' : ''}">
                                <div class="timeline-marker-col">
                                    <div class="timeline-dot"></div>
                                    ${i < steps.length - 1 ? '<div class="timeline-line"></div>' : ''}
                                </div>
                                <div class="timeline-content">
                                    <div class="timeline-title">${ui.esc(s.step)}</div>
                                    <div class="timeline-date">${s.date ? ui.formatDate(s.date) + (s.time ? ' · ' + s.time : '') : 'Pending'}</div>
                                </div>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
                <div class="btn-group">
                    <a href="#delivery/${o.order_id}" class="btn btn-secondary">🚚 Track Delivery</a>
                    ${isDelivered ? `<a href="#return/${o.order_id}" class="btn btn-secondary">↩️ Start Return</a>` : ''}
                    ${hasWarranty ? `<a href="#warranty-claim/${o.order_id}" class="btn btn-secondary">🛡️ Warranty Help</a>` : ''}
                    <button class="btn btn-primary" id="btnAskOrder">💬 Ask About This Order</button>
                </div>
            `;
            document.getElementById('btnAskOrder').onclick = () => {
                state.orderContext = o.order_id;
                window.location.hash = '#assist';
            };
        },

        /* ── DELIVERY ── */
        async delivery(el, orderId) {
            if (orderId) {
                const data = await api.get(`/api/orders/${orderId}`);
                if (!data || !data.order) { el.innerHTML = ui.empty('🚚', 'Order not found', ''); return; }
                const o = data.order;
                const steps = o.delivery_steps || [];
                el.innerHTML = `
                    <a href="#order/${orderId}" class="back-link">← Back to Order</a>
                    <h1 class="page-title">Delivery Tracking</h1>
                    <div class="card mb-lg">
                        <div class="flex items-center gap-lg mb-lg">
                            <span style="font-size:48px;">${o.image_placeholder}</span>
                            <div>
                                <h2 style="margin-bottom:4px;">${ui.esc(o.product_name)}</h2>
                                <div class="text-sm text-muted">${o.order_id} · ${ui.badge(o.status)}</div>
                            </div>
                        </div>
                        <div class="detail-grid mb-lg">
                            <div class="detail-item"><div class="detail-label">Courier</div><div class="detail-value">${ui.esc(o.courier)}</div></div>
                            <div class="detail-item"><div class="detail-label">Tracking ID</div><div class="detail-value">${ui.esc(o.tracking_id)}</div></div>
                            <div class="detail-item"><div class="detail-label">${o.delivered_date ? 'Delivered' : 'Expected Delivery'}</div><div class="detail-value">${ui.formatDate(o.delivered_date || o.expected_delivery)}</div></div>
                            <div class="detail-item"><div class="detail-label">Address</div><div class="detail-value">${ui.esc(o.delivery_address)}</div></div>
                        </div>
                        <h3>Shipment Progress</h3>
                        <div class="timeline">
                            ${steps.map((s, i) => {
                                const completed = s.completed;
                                const isCurrent = !completed && (i === 0 || steps[i - 1].completed);
                                return `<div class="timeline-item ${completed ? 'completed' : ''} ${isCurrent ? 'current' : ''}">
                                    <div class="timeline-marker-col">
                                        <div class="timeline-dot"></div>
                                        ${i < steps.length - 1 ? '<div class="timeline-line"></div>' : ''}
                                    </div>
                                    <div class="timeline-content">
                                        <div class="timeline-title">${ui.esc(s.step)}</div>
                                        <div class="timeline-date">${s.date ? ui.formatDate(s.date) + (s.time ? ' · ' + s.time : '') : 'Pending'}</div>
                                    </div>
                                </div>`;
                            }).join('')}
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-primary" onclick="Cartora.setOrderContext('${o.order_id}'); window.location.hash='#assist';">💬 Report Delivery Issue</button>
                    </div>
                `;
            } else {
                const data = await api.get('/api/orders');
                const orders = data ? (data.orders || []) : [];
                el.innerHTML = `
                    <h1 class="page-title">Delivery</h1>
                    <p class="page-subtitle">Track your shipments.</p>
                    ${orders.length > 0 ? `<div class="grid gap-md">${orders.map(o => `
                        <a href="#delivery/${o.order_id}" class="order-card">
                            <div class="order-emoji">${o.image_placeholder}</div>
                            <div class="order-details">
                                <div class="order-product-name">${ui.esc(o.product_name)}</div>
                                <div class="order-meta">${o.order_id} · ${ui.badge(o.status)}</div>
                            </div>
                            <div class="text-sm text-muted">${o.delivered_date ? 'Delivered ' + ui.formatDate(o.delivered_date) : 'Expected ' + ui.formatDate(o.expected_delivery)}</div>
                        </a>
                    `).join('')}</div>` : ui.empty('🚚', 'No deliveries', 'Place an order to track its delivery.', 'Browse Shop', 'shop')}
                `;
            }
        },

        /* ── RETURNS & REFUNDS ── */
        async returns(el) {
            const [ordersData, returnsData] = await Promise.all([api.get('/api/orders'), api.get('/api/returns')]);
            const orders = ordersData ? ordersData.orders || [] : [];
            const returns = returnsData ? returnsData.returns || [] : [];
            const delivered = orders.filter(o => o.status === 'Delivered');
            let activeTab = 'start';
            const render = () => {
                const startContent = delivered.length > 0 ? `<div class="grid gap-md">${delivered.map(o => {
                    const deadline = o.return_deadline ? new Date(o.return_deadline + 'T23:59:59') : null;
                    const eligible = deadline && deadline >= new Date();
                    return `<div class="card flex items-center justify-between">
                        <div class="flex items-center gap-md">
                            <span style="font-size:32px;">${o.image_placeholder}</span>
                            <div>
                                <div style="font-weight:600;">${ui.esc(o.product_name)}</div>
                                <div class="text-sm text-muted">${o.order_id} · Deadline: ${o.return_deadline ? ui.formatDate(o.return_deadline) : 'N/A'}</div>
                                <div class="mt-sm">${eligible ? '<span class="badge badge-success">Eligible</span>' : '<span class="badge badge-error">Window Expired</span>'}</div>
                            </div>
                        </div>
                        ${eligible ? `<a href="#return/${o.order_id}" class="btn btn-primary btn-sm">Start Return</a>` : '<span class="text-sm text-muted">Not eligible</span>'}
                    </div>`;
                }).join('')}</div>` : ui.empty('↩️', 'No delivered orders', 'Returns are available for delivered orders within the return window.');
                const returnsContent = returns.length > 0 ? `<div class="grid gap-md">${returns.map(r => `
                    <div class="card">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3>${ui.esc(r.product_name)}</h3>
                                <div class="text-sm text-muted">${r.return_id} · Order: ${r.order_id}</div>
                                <div class="text-sm text-muted mt-sm">Reason: ${ui.esc(r.reason)} · Condition: ${ui.esc(r.item_condition)}</div>
                            </div>
                            <div class="text-right">
                                ${ui.badge(r.status)}
                                <div class="text-sm text-muted mt-sm">Refund: ${ui.formatPrice(r.refund_amount)}</div>
                            </div>
                        </div>
                    </div>
                `).join('')}</div>` : ui.empty('📋', 'No return requests', 'You haven\'t initiated any returns yet.');
                document.getElementById('tabContent').innerHTML = activeTab === 'start' ? startContent : returnsContent;
            };
            el.innerHTML = `
                <h1 class="page-title">Returns & Refunds</h1>
                <div class="tabs">
                    <button class="tab active" data-tab="start">Start a Return</button>
                    <button class="tab" data-tab="returns">My Returns (${returns.length})</button>
                </div>
                <div id="tabContent"></div>
            `;
            render();
            el.querySelectorAll('.tab').forEach(t => {
                t.onclick = () => {
                    activeTab = t.dataset.tab;
                    el.querySelectorAll('.tab').forEach(tt => tt.classList.toggle('active', tt.dataset.tab === activeTab));
                    render();
                };
            });
        },

        /* ── RETURN FORM ── */
        async returnForm(el, orderId) {
            const eligData = await api.get(`/api/returns/eligibility/${orderId}`);
            const orderData = await api.get(`/api/orders/${orderId}`);
            if (!orderData || !orderData.order) { el.innerHTML = ui.empty('↩️', 'Order not found', ''); return; }
            const o = orderData.order;
            if (!eligData || !eligData.eligible) {
                el.innerHTML = `
                    <a href="#returns" class="back-link">← Back to Returns</a>
                    <div class="card">
                        <div class="flex items-center gap-lg mb-lg">
                            <span style="font-size:48px;">${o.image_placeholder}</span>
                            <div><h2>${ui.esc(o.product_name)}</h2><div class="text-sm text-muted">${o.order_id}</div></div>
                        </div>
                        <div class="badge badge-error mb-md">Not Eligible for Return</div>
                        <p>${eligData ? ui.esc(eligData.reason) : 'Unable to determine eligibility.'}</p>
                        <a href="#assist" class="btn btn-primary mt-md">💬 Ask Cartora Assist</a>
                    </div>`;
                return;
            }
            el.innerHTML = `
                <a href="#returns" class="back-link">← Back to Returns</a>
                <div class="card mb-lg">
                    <div class="flex items-center gap-lg mb-lg">
                        <span style="font-size:48px;">${o.image_placeholder}</span>
                        <div><h2>${ui.esc(o.product_name)}</h2><div class="text-sm text-muted">${o.order_id} · Return by ${ui.formatDate(eligData.deadline)}</div></div>
                    </div>
                    <span class="badge badge-success mb-lg">Eligible for Return</span>
                    <div class="form-group">
                        <label class="form-label">Reason for Return</label>
                        <select class="form-control" id="returnReason">
                            <option value="">Select a reason...</option>
                            <option value="Defective">Defective / Not working</option>
                            <option value="Not as described">Not as described</option>
                            <option value="Changed mind">Changed my mind</option>
                            <option value="Wrong item">Wrong item received</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Item Condition</label>
                        <select class="form-control" id="returnCondition">
                            <option value="">Select condition...</option>
                            <option value="Unused / sealed">Unused / sealed</option>
                            <option value="Used - good condition">Used - good condition</option>
                            <option value="Used - minor wear">Used - minor wear</option>
                            <option value="Damaged">Damaged</option>
                        </select>
                    </div>
                    <div class="card-flat p-md mb-lg">
                        <div class="text-sm text-muted">Refund Method</div>
                        <div style="font-weight:500;">${ui.esc(o.payment_method)} (original payment method)</div>
                        <div class="text-sm text-muted mt-sm">Refund Amount: <strong>${ui.formatPrice(o.price)}</strong></div>
                    </div>
                    <button class="btn btn-primary btn-lg btn-block" id="btnSubmitReturn">Submit Return Request</button>
                </div>
            `;
            document.getElementById('btnSubmitReturn').onclick = async () => {
                const reason = document.getElementById('returnReason').value;
                const condition = document.getElementById('returnCondition').value;
                if (!reason || !condition) { ui.toast('Please select a reason and item condition.', 'error'); return; }
                const btn = document.getElementById('btnSubmitReturn');
                btn.disabled = true; btn.textContent = 'Submitting...';
                const res = await api.post('/api/returns', { order_id: orderId, reason, item_condition: condition });
                if (res && res.return_request) {
                    ui.toast(`Return ${res.return_request.return_id} created successfully!`, 'success');
                    window.location.hash = '#returns';
                } else { btn.disabled = false; btn.textContent = 'Submit Return Request'; }
            };
        },

        /* ── WARRANTY & REPAIRS ── */
        async warranty(el) {
            const [ordersData, claimsData] = await Promise.all([api.get('/api/orders'), api.get('/api/warranty/claims')]);
            const orders = ordersData ? ordersData.orders || [] : [];
            const claims = claimsData ? claimsData.claims || [] : [];
            const withWarranty = orders.filter(o => o.warranty_months > 0);
            el.innerHTML = `
                <h1 class="page-title">Warranty & Repairs</h1>
                <p class="page-subtitle">Check warranty status and file claims for your products.</p>
                <h2>Products with Warranty</h2>
                ${withWarranty.length > 0 ? `<div class="grid gap-md mb-xl">${withWarranty.map(o => {
                    const wEnd = o.warranty_end ? new Date(o.warranty_end + 'T23:59:59') : null;
                    const active = wEnd && wEnd >= new Date();
                    const noWarrantyYet = !o.warranty_end && o.warranty_months > 0;
                    return `<div class="card flex items-center justify-between">
                        <div class="flex items-center gap-md">
                            <span style="font-size:32px;">${o.image_placeholder}</span>
                            <div>
                                <div style="font-weight:600;">${ui.esc(o.product_name)}</div>
                                <div class="text-sm text-muted">${o.order_id} · ${o.warranty_months} months warranty</div>
                                <div class="mt-sm">${noWarrantyYet ? '<span class="badge badge-warning">Not yet delivered</span>' : active ? `<span class="badge badge-success">Active until ${ui.formatDate(o.warranty_end)}</span>` : `<span class="badge badge-error">Expired ${ui.formatDate(o.warranty_end)}</span>`}</div>
                            </div>
                        </div>
                        ${active ? `<a href="#warranty-claim/${o.order_id}" class="btn btn-primary btn-sm">File Claim</a>` : '<span class="text-sm text-muted"></span>'}
                    </div>`;
                }).join('')}</div>` : ui.empty('🛡️', 'No warranted products', 'Products with warranty will appear here.')}
                ${claims.length > 0 ? `<h2>Warranty Claims</h2><div class="grid gap-md">${claims.map(c => `
                    <div class="card">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3>${ui.esc(c.product_name)}</h3>
                                <div class="text-sm text-muted">${c.claim_id} · Order: ${c.order_id}</div>
                                <div class="text-sm text-muted mt-sm">${ui.esc(c.issue_category)}: ${ui.esc(c.description)}</div>
                            </div>
                            <div class="text-right">${ui.badge(c.status)}<div class="text-xs text-muted mt-sm">${ui.formatDate(c.created_date)}</div></div>
                        </div>
                    </div>
                `).join('')}</div>` : ''}
            `;
        },

        /* ── WARRANTY CLAIM FORM ── */
        async warrantyClaim(el, orderId) {
            const [wData, orderData] = await Promise.all([api.get(`/api/warranty/status/${orderId}`), api.get(`/api/orders/${orderId}`)]);
            if (!orderData || !orderData.order) { el.innerHTML = ui.empty('🛡️', 'Order not found', ''); return; }
            const o = orderData.order;
            if (!wData || !wData.active) {
                el.innerHTML = `
                    <a href="#warranty" class="back-link">← Back to Warranty</a>
                    <div class="card">
                        <div class="flex items-center gap-lg mb-lg"><span style="font-size:48px;">${o.image_placeholder}</span><div><h2>${ui.esc(o.product_name)}</h2><div class="text-sm text-muted">${o.order_id}</div></div></div>
                        ${wData && !wData.has_warranty ? '<div class="badge badge-neutral mb-md">No Warranty</div><p>This product does not include a warranty.</p>' : wData ? `<div class="badge badge-error mb-md">Warranty Expired</div><p>${ui.esc(wData.reason || '')}</p>` : '<div class="badge badge-error mb-md">Unable to verify</div>'}
                        <a href="#assist" class="btn btn-primary mt-md">💬 Ask Cartora Assist</a>
                    </div>`;
                return;
            }
            el.innerHTML = `
                <a href="#warranty" class="back-link">← Back to Warranty</a>
                <div class="card mb-lg">
                    <div class="flex items-center gap-lg mb-lg"><span style="font-size:48px;">${o.image_placeholder}</span><div><h2>${ui.esc(o.product_name)}</h2><div class="text-sm text-muted">${o.order_id} · Warranty until ${ui.formatDate(wData.warranty_end)}</div></div></div>
                    <span class="badge badge-success mb-lg">Active Warranty</span>
                    <div class="form-group">
                        <label class="form-label">Issue Category</label>
                        <select class="form-control" id="claimCategory">
                            <option value="">Select category...</option>
                            <option value="Hardware defect">Hardware defect</option>
                            <option value="Software issue">Software issue</option>
                            <option value="Battery problem">Battery problem</option>
                            <option value="Connectivity issue">Connectivity issue</option>
                            <option value="Physical damage">Physical damage</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Describe the Issue</label>
                        <textarea class="form-control" id="claimDesc" placeholder="Describe the problem in detail..."></textarea>
                    </div>
                    <button class="btn btn-primary btn-lg btn-block" id="btnSubmitClaim">Submit Warranty Claim</button>
                </div>
            `;
            document.getElementById('btnSubmitClaim').onclick = async () => {
                const cat = document.getElementById('claimCategory').value;
                const desc = document.getElementById('claimDesc').value.trim();
                if (!cat || !desc) { ui.toast('Please fill in all fields.', 'error'); return; }
                const btn = document.getElementById('btnSubmitClaim');
                btn.disabled = true; btn.textContent = 'Submitting...';
                const res = await api.post('/api/warranty/claims', { order_id: orderId, issue_category: cat, description: desc });
                if (res && res.claim) {
                    ui.toast(`Warranty claim ${res.claim.claim_id} submitted!`, 'success');
                    window.location.hash = '#warranty';
                } else { btn.disabled = false; btn.textContent = 'Submit Warranty Claim'; }
            };
        },

        /* ── CARTORA ASSIST ── */
        async assist(contentEl) {
            const custKey = `cartora_convos_${state.customer.id}`;
            if (state.conversations.length === 0) {
                try { state.conversations = JSON.parse(localStorage.getItem(custKey) || '[]'); } catch(e) { state.conversations = []; }
            }
            const saveConvos = () => { try { localStorage.setItem(custKey, JSON.stringify(state.conversations)); } catch(e) {} };
            if (!state.activeConversationId && state.conversations.length === 0) {
                state.conversations.push({ id: Date.now().toString(), title: 'New Conversation', messages: [], created: new Date().toISOString() });
                state.activeConversationId = state.conversations[0].id;
            }
            if (!state.activeConversationId && state.conversations.length > 0) {
                state.activeConversationId = state.conversations[0].id;
            }

            contentEl.innerHTML = `
                <div class="chat-container">
                    <div class="chat-sidebar">
                        <div class="chat-sidebar-header">
                            <button class="btn btn-primary btn-sm btn-block" id="btnNewConvo">+ New Conversation</button>
                            <input type="text" class="chat-sidebar-search" id="convoSearch" placeholder="Search conversations...">
                        </div>
                        <div class="chat-sidebar-list" id="convoList"></div>
                    </div>
                    <div class="chat-main">
                        <div class="chat-messages" id="chatMessages"></div>
                        ${state.orderContext ? `<div style="padding:4px 24px 0;"><div class="order-context-badge">📦 Context: Order ${state.orderContext} <button id="clearCtx">✕</button></div></div>` : ''}
                        <div class="chat-composer">
                            <textarea id="chatInput" class="chat-input" placeholder="Ask about an order, product, delivery, return, refund, warranty or account issue..." rows="1"></textarea>
                            <button id="btnSend" class="chat-send-btn">↑</button>
                        </div>
                        <div class="diagnostics" id="diagBar" style="display:none; flex-wrap:wrap; gap:8px;">
                            <span class="text-xs text-muted">Dev:</span>
                            <div class="diag-item"><div class="diag-dot" id="diagMemDot"></div><span id="diagMemText"></span></div>
                            <div class="diag-item"><div class="diag-dot" id="diagSaveDot"></div><span id="diagSaveText"></span></div>
                            <div class="diag-item"><span id="diagTokensText" class="text-xs text-muted"></span></div>
                            <div class="diag-item"><span id="diagLatencyText" class="text-xs text-muted"></span></div>
                        </div>
                    </div>
                </div>
            `;

            const chatMessages = document.getElementById('chatMessages');
            const chatInput = document.getElementById('chatInput');
            const btnSend = document.getElementById('btnSend');
            const convoList = document.getElementById('convoList');

            const renderConvoList = () => {
                const now = new Date();
                const today = now.toDateString();
                const groups = { today: [], week: [], older: [] };
                state.conversations.forEach(c => {
                    const d = new Date(c.created);
                    if (d.toDateString() === today) groups.today.push(c);
                    else if ((now - d) / 86400000 < 7) groups.week.push(c);
                    else groups.older.push(c);
                });
                let html = '';
                if (groups.today.length) {
                    html += '<div class="chat-group-label">Today</div>';
                    groups.today.forEach(c => { html += `<div class="chat-list-item ${c.id === state.activeConversationId ? 'active' : ''}" data-id="${c.id}">${ui.esc(c.title)}</div>`; });
                }
                if (groups.week.length) {
                    html += '<div class="chat-group-label">Previous 7 days</div>';
                    groups.week.forEach(c => { html += `<div class="chat-list-item ${c.id === state.activeConversationId ? 'active' : ''}" data-id="${c.id}">${ui.esc(c.title)}</div>`; });
                }
                if (groups.older.length) {
                    html += '<div class="chat-group-label">Older</div>';
                    groups.older.forEach(c => { html += `<div class="chat-list-item ${c.id === state.activeConversationId ? 'active' : ''}" data-id="${c.id}">${ui.esc(c.title)}</div>`; });
                }
                convoList.innerHTML = html;
                convoList.querySelectorAll('.chat-list-item').forEach(item => {
                    item.onclick = () => {
                        state.activeConversationId = item.dataset.id;
                        renderConvoList();
                        renderMessages();
                    };
                });
            };

            const getActiveConvo = () => state.conversations.find(c => c.id === state.activeConversationId);

            const renderMessages = () => {
                const convo = getActiveConvo();
                if (!convo || convo.messages.length === 0) {
                    const caps = [
                        { icon: '📦', title: 'Orders', desc: 'Track orders, delivery status and purchase history', prompt: 'Where is my latest order?' },
                        { icon: '🚚', title: 'Delivery', desc: 'Shipping updates, delays and delivery issues', prompt: 'Why has my order not arrived yet?' },
                        { icon: '↩️', title: 'Returns', desc: 'Return eligibility, process and tracking', prompt: 'Can I return my AirPulse Pro earbuds?' },
                        { icon: '💰', title: 'Refunds', desc: 'Refund status, timelines and methods', prompt: 'When should my refund arrive?' },
                        { icon: '🛡️', title: 'Warranty', desc: 'Coverage status, claims and repairs', prompt: 'Is my earbuds warranty still active?' },
                        { icon: '🔧', title: 'Product Help', desc: 'Troubleshooting, setup and usage guidance', prompt: 'My left earbud is not charging. What should I try?' },
                        { icon: '💳', title: 'Payments', desc: 'Payment methods, billing and charges', prompt: 'Can I change my payment method?' },
                        { icon: '👤', title: 'Account', desc: 'Profile, preferences and account settings', prompt: 'What information do you know about my current plan?' }
                    ];
                    chatMessages.innerHTML = `
                        <div class="chat-home">
                            <div class="chat-home-icon">✦</div>
                            <h2>${ui.greeting()}, ${ui.esc(state.customer.name.split(' ')[0])}.</h2>
                            <p>Ask about your orders, deliveries, returns, refunds, warranty, products or account. I can use your Cartora support history when it is relevant.</p>
                            <div class="capabilities-grid">
                                ${caps.map(c => `<div class="capability-card" data-prompt="${ui.esc(c.prompt)}"><div class="capability-icon">${c.icon}</div><div class="capability-title">${c.title}</div><div class="capability-desc">${c.desc}</div></div>`).join('')}
                            </div>
                            <div class="chat-trust mt-lg">🔒 Order and eligibility facts come from Cartora data. Support memory is customer-specific.</div>
                        </div>
                    `;
                    chatMessages.querySelectorAll('.capability-card').forEach(card => {
                        card.onclick = () => { chatInput.value = card.dataset.prompt; chatInput.focus(); };
                    });
                } else {
                    chatMessages.innerHTML = convo.messages.map(m => `
                        <div class="message message-${m.role}">
                            <div class="message-bubble">${ui.esc(m.content)}</div>
                            <div class="message-time">${m.time || ''}</div>
                        </div>
                    `).join('');
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            };

            const sendMessage = async () => {
                const text = chatInput.value.trim();
                if (!text) return;
                chatInput.value = '';
                btnSend.disabled = true;
                const convo = getActiveConvo();
                if (!convo) return;
                if (convo.messages.length === 0) { convo.title = text.slice(0, 50) + (text.length > 50 ? '...' : ''); }
                convo.messages.push({ role: 'user', content: text, time: ui.timeNow() });
                renderMessages();
                renderConvoList();
                // Show typing
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message message-assistant';
                typingDiv.id = 'typing';
                typingDiv.innerHTML = '<div class="message-bubble"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>';
                chatMessages.appendChild(typingDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                try {
                    const body = { message: text, session_id: convo.id };
                    if (state.orderContext) body.order_context = state.orderContext;
                    const res = await api.post('/api/chat', body);
                    const el = document.getElementById('typing');
                    if (el) el.remove();
                    if (res && res.escalated && res.case_id) {
                        const banner = document.createElement('div');
                        banner.className = 'escalation-banner';
                        banner.style.backgroundColor = '#fff3cd';
                        banner.style.color = '#856404';
                        banner.style.padding = '10px';
                        banner.style.borderRadius = '5px';
                        banner.style.marginBottom = '15px';
                        banner.style.fontSize = '0.9rem';
                        banner.style.border = '1px solid #ffeeba';
                        banner.innerHTML = `<strong>⚠️ Case Escalated</strong><br>A human agent has been assigned. Case ID: ${res.case_id}`;
                        chatMessages.appendChild(banner);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        if (state.ordersView === 'cases') loadCases();
                    }
                    if (res && res.reply) {
                        convo.messages.push({ role: 'assistant', content: res.reply, time: ui.timeNow() });
                        state.lastDiag = { memories_used: res.memories_used, memory_saved: res.memory_saved };
                        const diagBar = document.getElementById('diagBar');
                        if (diagBar) {
                            diagBar.style.display = 'flex';
                            document.getElementById('diagMemDot').className = 'diag-dot ' + (res.memories_used > 0 ? 'diag-dot-success' : 'diag-dot-error');
                            document.getElementById('diagMemText').textContent = `Memories: ${res.memories_used}`;
                            document.getElementById('diagSaveDot').className = 'diag-dot ' + (res.memory_saved ? 'diag-dot-success' : 'diag-dot-error');
                            document.getElementById('diagSaveText').textContent = res.memory_saved ? 'Saved' : 'Not saved';
                            if (res.tokens) {
                                document.getElementById('diagTokensText').textContent = `Tokens: ${res.tokens.prompt_tokens}p + ${res.tokens.completion_tokens}c`;
                            }
                            if (res.latency_ms) {
                                document.getElementById('diagLatencyText').textContent = `Latency: ${res.latency_ms.recall}ms rcl + ${res.latency_ms.llm}ms llm + ${res.latency_ms.retain}ms ret (${res.latency_ms.total}ms tot)`;
                            }
                        }
                    } else {
                        convo.messages.push({ role: 'assistant', content: 'I apologize, but I was unable to process your request. Please try again.', time: ui.timeNow() });
                    }
                } catch (e) {
                    const el = document.getElementById('typing');
                    if (el) el.remove();
                    convo.messages.push({ role: 'assistant', content: 'There was an error communicating with the support service. Please try again.', time: ui.timeNow() });
                }
                saveConvos();
                renderMessages();
                btnSend.disabled = false;
                chatInput.focus();
            };

            btnSend.onclick = sendMessage;
            chatInput.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
            chatInput.oninput = () => { chatInput.style.height = 'auto'; chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px'; };

            document.getElementById('btnNewConvo').onclick = () => {
                const c = { id: Date.now().toString(), title: 'New Conversation', messages: [], created: new Date().toISOString() };
                state.conversations.unshift(c);
                state.activeConversationId = c.id;
                state.orderContext = null;
                saveConvos();
                renderConvoList();
                renderMessages();
            };

            if (document.getElementById('clearCtx')) {
                document.getElementById('clearCtx').onclick = () => { state.orderContext = null; document.querySelector('.order-context-badge')?.remove(); };
            }

            document.getElementById('convoSearch').oninput = (e) => {
                const q = e.target.value.toLowerCase();
                convoList.querySelectorAll('.chat-list-item').forEach(item => {
                    item.style.display = item.textContent.toLowerCase().includes(q) ? '' : 'none';
                });
            };

            renderConvoList();
            renderMessages();
        },

        /* ── MY CASES ── */
        async cases(el) {
            const data = await api.get('/api/cases');
            if (!data) return;
            const cases = data.cases || [];
            if (cases.length === 0) {
                el.innerHTML = `<h1 class="page-title">My Cases</h1>` + ui.empty('📋', 'No cases yet', 'Your return requests, warranty claims and support cases will appear here.', 'Ask Cartora Assist', 'assist');
                return;
            }
            el.innerHTML = `
                <h1 class="page-title">My Cases</h1>
                <p class="page-subtitle">${cases.length} case${cases.length !== 1 ? 's' : ''}</p>
                <div class="grid gap-md">
                    ${cases.map(c => `
                        <div class="card">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="flex items-center gap-md mb-sm">
                                        <h3 style="margin:0;">${ui.esc(c.case_id)}</h3>
                                        ${ui.badge(c.type)}
                                    </div>
                                    <div class="text-sm">${ui.esc(c.summary || c.product_name)}</div>
                                    <div class="text-xs text-muted mt-sm">Order: <a href="#order/${c.order_id}">${c.order_id}</a> · Created: ${ui.formatDate(c.created_date)}</div>
                                </div>
                                <div class="text-right">
                                    ${ui.badge(c.status)}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        },

        /* ── ACCOUNT ── */
        async account(el) {
            const c = state.customer;
            el.innerHTML = `
                <h1 class="page-title">Account</h1>
                <div class="card mb-lg">
                    <div class="profile-header">
                        <div class="avatar profile-avatar">${c.avatar_initials}</div>
                        <div class="profile-info">
                            <h2 style="margin-bottom:4px;">${ui.esc(c.name)}</h2>
                            <div class="flex items-center gap-sm">
                                ${ui.badge(c.tier)}
                                <span class="text-sm text-muted">Member since ${ui.formatDate(c.member_since)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="profile-detail"><span class="profile-detail-label">Email</span><span class="profile-detail-value">${ui.esc(c.email)}</span></div>
                    <div class="profile-detail"><span class="profile-detail-label">Phone</span><span class="profile-detail-value">${ui.esc(c.phone || '—')}</span></div>
                    <div class="profile-detail"><span class="profile-detail-label">City</span><span class="profile-detail-value">${ui.esc(c.city)}</span></div>
                    <div class="profile-detail"><span class="profile-detail-label">Saved Address</span><span class="profile-detail-value">${ui.esc(c.saved_address || '—')}</span></div>
                    <div class="profile-detail"><span class="profile-detail-label">Customer ID</span><span class="profile-detail-value">${ui.esc(c.id)}</span></div>
                </div>
                <div class="card card-flat p-md text-center">
                    <p class="text-sm text-muted mb-sm">This is a demo account for the Cartora hackathon prototype.</p>
                    <button class="btn btn-danger btn-sm" id="btnLogoutAcct">Logout</button>
                </div>
            `;
            document.getElementById('btnLogoutAcct').onclick = async () => { await api.post('/api/logout'); window.location.href = '/'; };
        }
    };

    /* ================================================================
       INIT
       ================================================================ */
    return {
        async init() {
            const data = await api.get('/api/me');
            if (!data || !data.customer) { window.location.href = '/'; return; }
            state.customer = data.customer;
            router.init();
        },
        setOrderContext(orderId) { state.orderContext = orderId; }
    };
})();

window.addEventListener('DOMContentLoaded', () => Cartora.init());
