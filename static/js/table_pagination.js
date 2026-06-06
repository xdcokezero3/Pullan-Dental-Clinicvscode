(function () {
    const PAGE_SIZE = 20;
    const PAGINATED_CLASS = 'table-page-hidden';
    const CONTROL_CLASS = 'table-pagination';

    function injectPaginationStyles() {
        if (document.getElementById('tablePaginationStyles')) return;

        const style = document.createElement('style');
        style.id = 'tablePaginationStyles';
        style.textContent = `
            .${PAGINATED_CLASS} { display: none !important; }
            .${CONTROL_CLASS} {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                flex-wrap: wrap;
                margin: 18px 0 4px;
            }
            .${CONTROL_CLASS} button {
                min-width: 38px;
                min-height: 36px;
                padding: 8px 12px;
                border: 1px solid #d9dee8;
                border-radius: 6px;
                background: #fff;
                color: #2f3a4a;
                cursor: pointer;
                font-weight: 600;
            }
            .${CONTROL_CLASS} button:hover:not(:disabled),
            .${CONTROL_CLASS} button.active {
                background: #2563eb;
                border-color: #2563eb;
                color: #fff;
            }
            .${CONTROL_CLASS} button:disabled {
                cursor: not-allowed;
                opacity: 0.45;
            }
            .${CONTROL_CLASS} .page-status {
                color: #6b7280;
                font-size: 13px;
                min-width: 130px;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    }

    function tableLabel(table) {
        return table.dataset.paginationLabel || 'entries';
    }

    function isFilterVisible(row) {
        return row.style.display !== 'none' && !row.hidden;
    }

    function pageButtons(totalPages, currentPage) {
        const pages = [];
        for (let page = 1; page <= totalPages; page += 1) {
            if (page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1) {
                pages.push(page);
            } else if (pages[pages.length - 1] !== '...') {
                pages.push('...');
            }
        }
        return pages;
    }

    function createPaginator(table) {
        const tbody = table.tBodies[0];
        if (!tbody || table.dataset.paginated === 'true' || table.dataset.noPagination === 'true') return;

        const oldPagination = table.closest('div')?.nextElementSibling;
        if (oldPagination && oldPagination.classList.contains('pagination')) {
            oldPagination.remove();
        }

        const rows = Array.from(tbody.rows);
        if (rows.length <= PAGE_SIZE) {
            watchSmallTable(table, tbody);
            return;
        }

        table.dataset.paginated = 'true';
        table.dataset.currentPage = '1';

        const controls = document.createElement('div');
        controls.className = CONTROL_CLASS;
        controls.setAttribute('aria-label', `${tableLabel(table)} pagination`);
        table.closest('div')?.insertAdjacentElement('afterend', controls);

        function render() {
            const allRows = Array.from(tbody.rows);
            const visibleRows = allRows.filter(isFilterVisible);
            const totalPages = Math.max(1, Math.ceil(visibleRows.length / PAGE_SIZE));
            let currentPage = parseInt(table.dataset.currentPage || '1', 10);

            if (Number.isNaN(currentPage) || currentPage < 1) currentPage = 1;
            if (currentPage > totalPages) currentPage = totalPages;
            table.dataset.currentPage = String(currentPage);

            allRows.forEach((row) => row.classList.remove(PAGINATED_CLASS));
            visibleRows.forEach((row, index) => {
                const page = Math.floor(index / PAGE_SIZE) + 1;
                row.classList.toggle(PAGINATED_CLASS, page !== currentPage);
            });

            controls.innerHTML = '';
            if (visibleRows.length <= PAGE_SIZE) {
                controls.style.display = 'none';
                return;
            }

            controls.style.display = 'flex';

            const previous = document.createElement('button');
            previous.type = 'button';
            previous.innerHTML = '&laquo;';
            previous.disabled = currentPage === 1;
            previous.title = 'Previous page';
            previous.addEventListener('click', () => {
                table.dataset.currentPage = String(currentPage - 1);
                render();
            });
            controls.appendChild(previous);

            pageButtons(totalPages, currentPage).forEach((page) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = page;
                if (page === '...') {
                    button.disabled = true;
                } else {
                    button.classList.toggle('active', page === currentPage);
                    button.addEventListener('click', () => {
                        table.dataset.currentPage = String(page);
                        render();
                    });
                }
                controls.appendChild(button);
            });

            const next = document.createElement('button');
            next.type = 'button';
            next.innerHTML = '&raquo;';
            next.disabled = currentPage === totalPages;
            next.title = 'Next page';
            next.addEventListener('click', () => {
                table.dataset.currentPage = String(currentPage + 1);
                render();
            });
            controls.appendChild(next);

            const start = ((currentPage - 1) * PAGE_SIZE) + 1;
            const end = Math.min(currentPage * PAGE_SIZE, visibleRows.length);
            const status = document.createElement('span');
            status.className = 'page-status';
            status.textContent = `${start}-${end} of ${visibleRows.length}`;
            controls.appendChild(status);
        }

        let renderQueued = false;
        const queueRender = () => {
            if (renderQueued) return;
            renderQueued = true;
            requestAnimationFrame(() => {
                renderQueued = false;
                render();
            });
        };

        const observer = new MutationObserver((mutations) => {
            const shouldReset = mutations.some((mutation) => mutation.type === 'childList' || mutation.attributeName === 'style');
            if (shouldReset) {
                table.dataset.currentPage = '1';
                queueRender();
            }
        });

        observer.observe(tbody, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style']
        });

        render();
    }

    function watchSmallTable(table, tbody) {
        if (table.dataset.paginationWatch === 'true') return;

        table.dataset.paginationWatch = 'true';
        const observer = new MutationObserver(() => {
            if (tbody.rows.length > PAGE_SIZE) {
                observer.disconnect();
                delete table.dataset.paginationWatch;
                createPaginator(table);
            }
        });

        observer.observe(tbody, { childList: true });
    }

    function initializePaginatedTables() {
        injectPaginationStyles();
        document.querySelectorAll('table').forEach(createPaginator);
    }

    document.addEventListener('DOMContentLoaded', initializePaginatedTables);
    window.refreshTablePagination = initializePaginatedTables;
})();
