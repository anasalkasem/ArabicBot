// تحديث البيانات تلقائياً
async function updateDashboard() {
    try {
        // جلب حالة البوت
        const response = await fetch('/status');
        const data = await response.json();
        
        // تحديث حالة البوت
        const statusBadge = document.getElementById('bot-status');
        statusBadge.textContent = getStatusText(data.bot_status);
        statusBadge.className = 'value status-badge ' + data.bot_status;
        
        // تحديث البيانات
        document.getElementById('iterations').textContent = data.iterations || '0';
        document.getElementById('start-time').textContent = formatTime(data.start_time);
        document.getElementById('last-check').textContent = formatTime(data.last_check);
        document.getElementById('open-positions').textContent = data.open_positions || '0';
        
        // تحديث الصفقات المفتوحة
        updatePositions(data.positions);
        
        // تحديث وقت التحديث
        document.getElementById('update-time').textContent = new Date().toLocaleString('ar-EG');
        
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function getStatusText(status) {
    const statusMap = {
        'running': 'يعمل 🟢',
        'stopped': 'متوقف 🔴',
        'initializing': 'جاري التشغيل... 🟡',
        'error': 'خطأ ❌'
    };
    return statusMap[status] || 'غير معروف';
}

function formatTime(timestamp) {
    if (!timestamp) return '-';
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('ar-EG', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch {
        return timestamp;
    }
}

function updatePositions(positions) {
    const container = document.getElementById('positions-container');
    
    if (!positions || positions.length === 0) {
        container.innerHTML = '<p class="no-positions">لا توجد صفقات مفتوحة حالياً</p>';
        return;
    }
    
    container.innerHTML = positions.map(pos => `
        <div class="position-item">
            <div class="position-header">
                <span class="position-symbol">${pos.symbol}</span>
                <span class="profit ${pos.current_profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                    ${pos.current_profit >= 0 ? '+' : ''}${pos.current_profit.toFixed(2)}%
                </span>
            </div>
            <div class="position-details">
                <div><strong>سعر الدخول:</strong> $${pos.entry_price.toFixed(2)}</div>
                <div><strong>الكمية:</strong> ${pos.quantity.toFixed(6)}</div>
                <div><strong>Stop-Loss:</strong> $${pos.stop_loss.toFixed(2)}</div>
                <div><strong>Take-Profit:</strong> $${pos.take_profit.toFixed(2)}</div>
            </div>
        </div>
    `).join('');
}

// تحديث السجلات
async function updateLogs() {
    try {
        const response = await fetch('/logs');
        const data = await response.json();
        
        const logsContainer = document.getElementById('logs');
        if (data.logs && data.logs.length > 0) {
            logsContainer.innerHTML = data.logs.map(log => `<p>${log}</p>`).join('');
            // التمرير للأسفل
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

// تحديث البيانات كل 5 ثواني
setInterval(updateDashboard, 5000);
setInterval(updateLogs, 10000);

// تحديث أولي
updateDashboard();
updateLogs();
