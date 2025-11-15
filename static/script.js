// تحديث البيانات تلقائياً
async function updateDashboard() {
    try {
        const response = await fetch('/status');
        const data = await response.json();
        
        // تحديث حالة البوت
        const statusBadge = document.getElementById('bot-status');
        statusBadge.textContent = getStatusText(data.bot_status);
        statusBadge.className = 'value status-badge ' + data.bot_status;
        
        // تحديث وضع التداول (TESTNET أو LIVE)
        const modeBadge = document.getElementById('mode');
        if (modeBadge && data.testnet !== undefined) {
            modeBadge.textContent = data.testnet ? 'TESTNET' : 'LIVE';
            modeBadge.className = data.testnet ? 'value mode-badge testnet' : 'value mode-badge live';
        }
        
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
        console.error('خطأ في جلب البيانات:', error);
        showToast('خطأ في الاتصال بالخادم', 'error');
    }
    
    // تحديث الإحصائيات
    updateStatistics();
}

async function updateStatistics() {
    try {
        const response = await fetch('/statistics');
        const stats = await response.json();
        
        if (stats.error) return;
        
        document.getElementById('total-trades').textContent = stats.total_trades || 0;
        document.getElementById('win-rate').textContent = (stats.win_rate || 0).toFixed(1) + '%';
        
        const profitElement = document.getElementById('total-profit');
        const profit = stats.total_profit_usd || 0;
        profitElement.textContent = '$' + profit.toFixed(2);
        profitElement.className = 'stat-value profit ' + (profit >= 0 ? 'positive' : 'negative');
        
        const todayTrades = (stats.today && stats.today.trades) ? stats.today.trades : 0;
        document.getElementById('today-trades').textContent = todayTrades;
        
    } catch (error) {
        console.error('خطأ في جلب الإحصائيات:', error.message || error);
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
    
    if (!positions || Object.keys(positions).length === 0) {
        container.innerHTML = '<p class="no-positions">لا توجد صفقات مفتوحة حالياً</p>';
        return;
    }
    
    // تحويل الـ object إلى array
    const positionsArray = Object.values(positions);
    
    container.innerHTML = positionsArray.map(pos => `
        <div class="position-item">
            <div class="position-header">
                <span class="position-symbol">${pos.symbol}</span>
                <span class="profit ${pos.current_profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                    ${pos.current_profit >= 0 ? '+' : ''}${pos.current_profit ? pos.current_profit.toFixed(2) : '0.00'}%
                </span>
            </div>
            <div class="position-details">
                <div><strong>سعر الدخول:</strong> $${pos.entry_price ? pos.entry_price.toFixed(2) : '0.00'}</div>
                <div><strong>الكمية:</strong> ${pos.quantity ? pos.quantity.toFixed(6) : '0.000000'}</div>
                <div><strong>Stop-Loss:</strong> $${pos.stop_loss ? pos.stop_loss.toFixed(2) : '0.00'}</div>
                <div><strong>Take-Profit:</strong> $${pos.take_profit ? pos.take_profit.toFixed(2) : '0.00'}</div>
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
            logsContainer.innerHTML = data.logs.map(log => 
                `<p>${escapeHtml(log)}</p>`
            ).join('');
            // التمرير للأسفل
            logsContainer.scrollTop = logsContainer.scrollHeight;
        } else {
            logsContainer.innerHTML = '<p class="loading">لا توجد سجلات متاحة</p>';
        }
    } catch (error) {
        console.error('خطأ في جلب السجلات:', error);
    }
}

// دوال الأزرار
function refreshData() {
    showToast('جاري تحديث البيانات...', 'info');
    updateDashboard();
    updateLogs();
    setTimeout(() => {
        showToast('تم التحديث بنجاح! ✅', 'success');
    }, 500);
}

function toggleLogs() {
    const logsSection = document.getElementById('logs-section');
    if (logsSection.style.display === 'none') {
        logsSection.style.display = 'block';
        showToast('تم إظهار السجلات', 'info');
    } else {
        logsSection.style.display = 'none';
        showToast('تم إخفاء السجلات', 'info');
    }
}

function clearLogsDisplay() {
    const logsContainer = document.getElementById('logs');
    logsContainer.innerHTML = '<p class="loading">تم مسح العرض - سيتم التحديث تلقائياً</p>';
    showToast('تم مسح السجلات المعروضة', 'info');
    setTimeout(updateLogs, 2000);
}

function exportLogs() {
    fetch('/logs')
        .then(response => response.json())
        .then(data => {
            if (data.logs && data.logs.length > 0) {
                const logsText = data.logs.join('\n');
                const blob = new Blob([logsText], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `bot-logs-${new Date().toISOString().slice(0,10)}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showToast('تم تصدير السجلات! 💾', 'success');
            } else {
                showToast('لا توجد سجلات للتصدير', 'error');
            }
        })
        .catch(error => {
            console.error('خطأ في تصدير السجلات:', error);
            showToast('فشل تصدير السجلات', 'error');
        });
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    
    // تغيير اللون حسب النوع
    if (type === 'success') {
        toast.style.background = '#10b981';
    } else if (type === 'error') {
        toast.style.background = '#ef4444';
    } else if (type === 'info') {
        toast.style.background = '#3b82f6';
    }
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// تحديث البيانات كل 5 ثواني
let updateInterval = setInterval(updateDashboard, 5000);
let logsInterval = setInterval(updateLogs, 10000);

// تحديث أولي
updateDashboard();
updateLogs();

// إيقاف التحديث عند إخفاء الصفحة (توفير الموارد)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        clearInterval(updateInterval);
        clearInterval(logsInterval);
    } else {
        updateInterval = setInterval(updateDashboard, 5000);
        logsInterval = setInterval(updateLogs, 10000);
        refreshData();
    }
});

// رسالة ترحيب
setTimeout(() => {
    showToast('مرحباً! يتم تحديث البيانات تلقائياً كل 5 ثواني 👋', 'success');
}, 1000);
