document.addEventListener('DOMContentLoaded', function() {
    var lineItems = document.getElementById('line-items');
    var addBtn = document.getElementById('add-item-btn');

    if (!lineItems || !addBtn) return;

    addBtn.addEventListener('click', function() {
        var row = document.createElement('div');
        row.className = 'line-item grid grid-cols-12 gap-3 mb-3 items-end';
        row.innerHTML = '<div class="col-span-6">' +
            '<input type="text" name="description[]" required class="w-full border-gray-300 rounded-md shadow-sm text-sm p-2 border">' +
            '</div>' +
            '<div class="col-span-2">' +
            '<input type="number" name="quantity[]" value="1" step="0.01" min="0" required class="w-full border-gray-300 rounded-md shadow-sm text-sm p-2 border item-qty">' +
            '</div>' +
            '<div class="col-span-2">' +
            '<input type="number" name="unit_price[]" value="0" step="0.01" min="0" required class="w-full border-gray-300 rounded-md shadow-sm text-sm p-2 border item-price">' +
            '</div>' +
            '<div class="col-span-2 flex items-center gap-2">' +
            '<span class="item-total text-sm font-medium text-gray-700 w-20"></span>' +
            '<button type="button" class="remove-item-btn text-red-500 hover:text-red-700 text-lg font-bold">&times;</button>' +
            '</div>';
        lineItems.appendChild(row);
        recalculate();
    });

    lineItems.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-item-btn')) {
            var items = lineItems.querySelectorAll('.line-item');
            if (items.length > 1) {
                e.target.closest('.line-item').remove();
                recalculate();
            }
        }
    });

    lineItems.addEventListener('input', function(e) {
        if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
            recalculate();
        }
    });

    var taxRateInput = document.getElementById('tax_rate');
    if (taxRateInput) {
        taxRateInput.addEventListener('input', recalculate);
    }

    function recalculate() {
        var items = lineItems.querySelectorAll('.line-item');
        var subtotal = 0;

        items.forEach(function(item) {
            var qty = parseFloat(item.querySelector('.item-qty').value) || 0;
            var price = parseFloat(item.querySelector('.item-price').value) || 0;
            var amount = qty * price;
            subtotal += amount;
            var totalSpan = item.querySelector('.item-total');
            if (totalSpan) {
                totalSpan.textContent = '$' + amount.toFixed(2);
            }
        });

        var taxRate = parseFloat(document.getElementById('tax_rate').value) || 0;
        var taxAmount = subtotal * (taxRate / 100);
        var total = subtotal + taxAmount;

        var subtotalEl = document.getElementById('subtotal');
        var taxEl = document.getElementById('tax-amount');
        var totalEl = document.getElementById('total');

        if (subtotalEl) subtotalEl.textContent = subtotal.toFixed(2);
        if (taxEl) taxEl.textContent = taxAmount.toFixed(2);
        if (totalEl) totalEl.textContent = total.toFixed(2);
    }

    recalculate();
});
