// Interactive Booking Calendar and Slot Selection
document.addEventListener('DOMContentLoaded', () => {
    const courtId = document.getElementById('court-id')?.value;
    const dateInput = document.getElementById('booking-date');
    const slotContainer = document.getElementById('slots-container');
    const startInput = document.getElementById('start-time-input');
    const endInput = document.getElementById('end-time-input');
    
    // Pricing elements
    const checkoutSection = document.getElementById('checkout-section');
    const summaryCourtCost = document.getElementById('summary-court-cost');
    const summaryRentalCost = document.getElementById('summary-rental-cost');
    const summaryDiscount = document.getElementById('summary-discount');
    const summaryTotal = document.getElementById('summary-total');
    const promoCodeInput = document.getElementById('promo-code-input');
    const applyPromoBtn = document.getElementById('apply-promo-btn');
    
    let selectedStart = null;
    let selectedEnd = null;
    
    if (dateInput && courtId) {
        // Fetch slots on date change
        dateInput.addEventListener('change', fetchSlots);
        // Initial fetch
        fetchSlots();
    }
    
    // Listen for rental quantity changes
    const rentalInputs = document.querySelectorAll('.rental-qty-input');
    rentalInputs.forEach(input => {
        input.addEventListener('change', () => {
            if (selectedStart !== null && selectedEnd !== null) {
                updatePrice();
            }
        });
    });
    
    // Promo code handler
    if (applyPromoBtn) {
        applyPromoBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (selectedStart !== null && selectedEnd !== null) {
                updatePrice();
            } else {
                alert('Please select your booking time slots first.');
            }
        });
    }

    async function fetchSlots() {
        const selectedDate = dateInput.value;
        if (!selectedDate) return;
        
        slotContainer.innerHTML = '<div style="grid-column: 1/-1; text-align:center;"><i class="fas fa-spinner fa-spin"></i> Loading slots...</div>';
        selectedStart = null;
        selectedEnd = null;
        startInput.value = '';
        endInput.value = '';
        checkoutSection.style.display = 'none';
        
        try {
            const response = await fetch(`/api/slots?court_id=${courtId}&date=${selectedDate}`);
            const data = await response.json();
            
            if (data.error) {
                slotContainer.innerHTML = `<div class="text-danger" style="grid-column: 1/-1;">Error: ${data.error}</div>`;
                return;
            }
            
            renderSlots(data.slots);
        } catch (error) {
            slotContainer.innerHTML = '<div class="text-danger" style="grid-column: 1/-1;">Failed to load slots. Please try again.</div>';
        }
    }
    
    function renderSlots(slots) {
        slotContainer.innerHTML = '';
        
        slots.forEach(slot => {
            const card = document.createElement('div');
            card.className = `slot-card ${slot.status}`;
            card.dataset.hour = slot.hour;
            
            let iconHtml = '';
            if (slot.status === 'booked') iconHtml = '<i class="fas fa-lock" style="display:block; margin-bottom:4px;"></i>';
            else if (slot.status === 'maintenance') iconHtml = '<i class="fas fa-tools" style="display:block; margin-bottom:4px;"></i>';
            else if (slot.is_peak) iconHtml = '<i class="fas fa-fire text-warning" style="font-size:10px; margin-right:4px;"></i>';
            
            card.innerHTML = `${iconHtml}<span>${slot.time_str}</span>`;
            
            if (slot.status === 'available') {
                card.addEventListener('click', () => handleSlotClick(slot.hour, slots));
            }
            
            slotContainer.appendChild(card);
        });
    }
    
    function handleSlotClick(hour, slots) {
        if (selectedStart === null || (selectedStart !== null && selectedEnd !== null)) {
            // First click or reset
            selectedStart = hour;
            selectedEnd = hour + 1;
        } else {
            // Second click
            if (hour < selectedStart) {
                selectedStart = hour;
                selectedEnd = selectedStart + 1;
            } else {
                selectedEnd = hour + 1;
                
                // Verify no booked/maintenance slots in between
                let invalidRange = false;
                for (let h = selectedStart; h < selectedEnd; h++) {
                    const slotData = slots.find(s => s.hour === h);
                    if (!slotData || slotData.status !== 'available') {
                        invalidRange = true;
                        break;
                    }
                }
                
                if (invalidRange) {
                    alert('Selected range includes unavailable slots. Please select a continuous available slot.');
                    selectedStart = hour;
                    selectedEnd = hour + 1;
                }
            }
        }
        
        // Highlight selected slots in UI
        const slotCards = slotContainer.querySelectorAll('.slot-card');
        slotCards.forEach(card => {
            const h = parseInt(card.dataset.hour);
            card.classList.remove('selected');
            if (selectedStart !== null && selectedEnd !== null) {
                if (h >= selectedStart && h < selectedEnd) {
                    card.classList.add('selected');
                }
            } else if (selectedStart !== null && h === selectedStart) {
                card.classList.add('selected');
            }
        });
        
        // Update form inputs
        startInput.value = selectedStart;
        endInput.value = selectedEnd;
        
        // Update price
        updatePrice();
    }
    
    async function updatePrice() {
        if (selectedStart === null || selectedEnd === null) {
            checkoutSection.style.display = 'none';
            return;
        }
        
        // Gather rentals
        const rentals = [];
        const rentalInputs = document.querySelectorAll('.rental-qty-input');
        rentalInputs.forEach(input => {
            const qty = parseInt(input.value) || 0;
            if (qty > 0) {
                rentals.push({
                    equipment_id: input.dataset.eqId,
                    quantity: qty
                });
            }
        });
        
        const payload = {
            court_id: parseInt(courtId),
            date: dateInput.value,
            start_time: selectedStart,
            end_time: selectedEnd,
            promo_code: promoCodeInput.value.trim(),
            rentals: rentals
        };
        
        try {
            const response = await fetch('/api/price-check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Render prices
            summaryCourtCost.textContent = `Rs. ${data.court_cost.toFixed(2)}`;
            summaryRentalCost.textContent = `Rs. ${data.rental_cost.toFixed(2)}`;
            summaryDiscount.textContent = `-Rs. ${data.discount.toFixed(2)}`;
            summaryTotal.textContent = `Rs. ${data.total.toFixed(2)}`;
            
            checkoutSection.style.display = 'block';
        } catch (error) {
            console.error('Price calculation failed:', error);
        }
    }
});
