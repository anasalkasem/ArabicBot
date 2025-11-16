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
        
        // تحديث حالة زر التداول
        const tradingBtn = document.getElementById('toggle-trading-btn');
        const tradingIcon = document.getElementById('trading-icon');
        const tradingText = document.getElementById('trading-text');
        if (tradingBtn && data.trading_enabled !== undefined) {
            if (data.trading_enabled) {
                tradingIcon.textContent = '⏸️';
                tradingText.textContent = 'إيقاف التداول';
                tradingBtn.className = 'btn btn-trading btn-stop';
            } else {
                tradingIcon.textContent = '▶️';
                tradingText.textContent = 'بدء التداول';
                tradingBtn.className = 'btn btn-trading btn-start';
            }
        }
        
        // تحديث البيانات
        document.getElementById('iterations').textContent = data.iterations || '0';
        document.getElementById('start-time').textContent = formatTime(data.start_time);
        document.getElementById('last-check').textContent = formatTime(data.last_check);
        document.getElementById('open-positions').textContent = data.open_positions || '0';
        
        // تحديث الصفقات المفتوحة
        updatePositions(data.positions);
        
        // تحديث حالة السوق (Market Regime)
        updateMarketRegime(data);
        
        // تحديث مؤشر الزخم المخصص
        updateCustomMomentum(data);
        
        // تحديث نظام السرب الذكي
        updateSwarmData();
        updateCausalData();
        
        // تحديث وقت التحديث
        document.getElementById('update-time').textContent = new Date().toLocaleString('ar-EG');
        
    } catch (error) {
        console.error('خطأ في جلب البيانات:', error);
        showToast('خطأ في الاتصال بالخادم', 'error');
    }
    
    // تحديث الإحصائيات
    updateStatistics();
}

function updateMarketRegime(data) {
    if (!data.regime_enabled) {
        document.getElementById('regime-card-container').style.display = 'none';
        return;
    }
    
    document.getElementById('regime-card-container').style.display = 'block';
    
    const regime = data.market_regime || 'sideways';
    const regimeData = {
        'bull': {
            icon: '🐂',
            name: 'BULL',
            description: 'السوق في اتجاه صاعد',
            strategy: 'استراتيجية جريئة - Buy the Dip',
            className: 'bull'
        },
        'bear': {
            icon: '🐻',
            name: 'BEAR',
            description: 'السوق في اتجاه هابط',
            strategy: 'استراتيجية حذرة - حماية رأس المال',
            className: 'bear'
        },
        'sideways': {
            icon: '↔️',
            name: 'SIDEWAYS',
            description: 'السوق في حالة تذبذب جانبي',
            strategy: 'استراتيجية متوازنة - BB Bands',
            className: 'sideways'
        }
    };
    
    const current = regimeData[regime] || regimeData['sideways'];
    
    document.getElementById('regime-icon').textContent = current.icon;
    document.getElementById('regime-name').textContent = current.name;
    document.getElementById('regime-description').textContent = current.description;
    document.getElementById('regime-strategy').textContent = current.strategy;
    
    const badge = document.getElementById('regime-badge');
    badge.className = 'regime-badge ' + current.className;
}

function updateCustomMomentum(data) {
    if (!data.momentum_enabled || !data.momentum_data) {
        document.getElementById('momentum-card-container').style.display = 'none';
        return;
    }
    
    document.getElementById('momentum-card-container').style.display = 'block';
    
    const firstSymbol = Object.keys(data.momentum_data)[0];
    if (!firstSymbol) return;
    
    const momentumData = data.momentum_data[firstSymbol];
    const index = momentumData.index || 50;
    const components = momentumData.components || {};
    
    document.getElementById('momentum-value').textContent = index.toFixed(1);
    
    let signalText = 'محايد';
    let signalClass = 'neutral';
    if (index < 20) {
        signalText = '🟢 شراء قوي!';
        signalClass = 'buy-strong';
    } else if (index < 40) {
        signalText = '🟢 شراء';
        signalClass = 'buy';
    } else if (index > 80) {
        signalText = '🔴 بيع قوي!';
        signalClass = 'sell-strong';
    } else if (index > 60) {
        signalText = '🟡 بيع';
        signalClass = 'sell';
    }
    
    const signalElement = document.getElementById('momentum-signal');
    signalElement.textContent = signalText;
    signalElement.className = 'momentum-signal ' + signalClass;
    
    if (components.technical) {
        document.getElementById('tech-score').textContent = components.technical.score.toFixed(1);
    }
    if (components.sentiment) {
        document.getElementById('sentiment-score').textContent = components.sentiment.score.toFixed(1);
    }
    if (components.volume) {
        document.getElementById('volume-score').textContent = components.volume.score.toFixed(1);
    }
    if (components.relative_strength) {
        document.getElementById('strength-score').textContent = components.relative_strength.score.toFixed(1);
    }
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
        'paused': 'متوقف مؤقتاً ⏸️',
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
    
    container.innerHTML = positionsArray.map(pos => {
        const positionType = pos.position_type || 'SPOT';
        const leverage = pos.leverage || 1;
        const liquidationPrice = pos.liquidation_price;
        
        let typeColor, typeIcon, typeText;
        if (positionType === 'LONG' || positionType === 'BUY') {
            typeColor = '#10b981';
            typeIcon = '🟢';
            typeText = 'LONG';
        } else if (positionType === 'SHORT' || positionType === 'SELL') {
            typeColor = '#ef4444';
            typeIcon = '🔴';
            typeText = 'SHORT';
        } else {
            typeColor = '#6b7280';
            typeIcon = '⚪';
            typeText = 'SPOT';
        }
        
        return `
        <div class="position-item">
            <div class="position-header">
                <div class="position-title">
                    <span class="position-type-badge" style="background: ${typeColor};">
                        ${typeIcon} ${typeText}
                    </span>
                    <span class="position-symbol">${pos.symbol}</span>
                    ${leverage > 1 ? `<span class="leverage-badge">${leverage}x</span>` : ''}
                </div>
                <span class="profit ${pos.current_profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                    ${pos.current_profit >= 0 ? '+' : ''}${pos.current_profit ? pos.current_profit.toFixed(2) : '0.00'}%
                </span>
            </div>
            <div class="position-details">
                <div><strong>سعر الدخول:</strong> $${pos.entry_price ? pos.entry_price.toFixed(2) : '0.00'}</div>
                <div><strong>الكمية:</strong> ${pos.quantity ? pos.quantity.toFixed(6) : '0.000000'}</div>
                <div><strong>Stop-Loss:</strong> $${pos.stop_loss ? pos.stop_loss.toFixed(2) : '0.00'}</div>
                <div><strong>Take-Profit:</strong> $${pos.take_profit ? pos.take_profit.toFixed(2) : '0.00'}</div>
                ${liquidationPrice ? `<div class="liquidation-row"><strong>🛡️ سعر التصفية:</strong> <span class="liquidation-price">$${liquidationPrice.toFixed(2)}</span></div>` : ''}
            </div>
        </div>
        `;
    }).join('');
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

async function toggleTrading() {
    const btn = document.getElementById('toggle-trading-btn');
    const icon = document.getElementById('trading-icon');
    const text = document.getElementById('trading-text');
    
    btn.disabled = true;
    
    try {
        const response = await fetch('/toggle-trading', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.trading_enabled) {
                icon.textContent = '⏸️';
                text.textContent = 'إيقاف التداول';
                btn.className = 'btn btn-trading btn-stop';
                showToast('✅ تم بدء التداول بنجاح', 'success');
            } else {
                icon.textContent = '▶️';
                text.textContent = 'بدء التداول';
                btn.className = 'btn btn-trading btn-start';
                showToast('⏸️ تم إيقاف التداول مؤقتاً', 'warning');
            }
            
            setTimeout(() => {
                updateDashboard();
            }, 500);
        } else {
            showToast('❌ خطأ: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('خطأ في تبديل حالة التداول:', error);
        showToast('❌ خطأ في الاتصال بالخادم', 'error');
    } finally {
        btn.disabled = false;
    }
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

// بيع جميع الصفقات
async function sellAllPositions() {
    if (!confirm('⚠️ هل أنت متأكد من بيع جميع الصفقات المفتوحة؟\n\nسيتم بيع كل الصفقات بالسعر الحالي.')) {
        return;
    }
    
    const sellBtn = document.getElementById('sell-all-btn');
    const originalText = sellBtn.innerHTML;
    
    try {
        sellBtn.disabled = true;
        sellBtn.innerHTML = '<span class="btn-icon">⏳</span><span>جاري البيع...</span>';
        
        const response = await fetch('/sell-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.sold > 0) {
                showToast(`✅ تم بيع ${data.sold} من ${data.total} صفقات بنجاح!`, 'success');
                
                if (data.results && data.results.length > 0) {
                    let details = '\n\nالتفاصيل:\n';
                    data.results.forEach(result => {
                        if (result.success) {
                            details += `✅ ${result.symbol}: ${result.profit_pct > 0 ? '+' : ''}${result.profit_pct}% ($${result.profit_usd > 0 ? '+' : ''}${result.profit_usd})\n`;
                        } else {
                            details += `❌ ${result.symbol}: فشل البيع (${result.error})\n`;
                        }
                    });
                    console.log(details);
                }
                
                if (data.failed > 0) {
                    showToast(`⚠️ فشل بيع ${data.failed} صفقة. تحقق من السجلات.`, 'error');
                }
            } else {
                showToast('📭 لا توجد صفقات مفتوحة للبيع', 'info');
            }
            
            setTimeout(() => {
                refreshData();
            }, 2000);
        } else {
            showToast(`❌ خطأ: ${data.error || 'فشل البيع'}`, 'error');
        }
        
    } catch (error) {
        console.error('Error selling all positions:', error);
        showToast('❌ خطأ في الاتصال بالخادم', 'error');
    } finally {
        sellBtn.disabled = false;
        sellBtn.innerHTML = originalText;
    }
}

// رسالة ترحيب
setTimeout(() => {
    showToast('مرحباً! يتم تحديث البيانات تلقائياً كل 5 ثواني 👋', 'success');
}, 1000);

// تحديث بيانات نظام السرب
async function updateSwarmData() {
    try {
        const response = await fetch('/swarm-stats');
        const data = await response.json();
        
        const swarmContainer = document.getElementById('swarm-card-container');
        
        if (data.success && data.enabled) {
            swarmContainer.style.display = 'block';
            
            const stats = data.stats;
            
            // تحديث الحالة
            if (stats.total_bots) {
                document.getElementById('swarm-status-text').textContent = 
                    `${stats.total_bots} بوت نشط`;
            }
            
            // تحديث أفضل بوت
            if (stats.top_performer) {
                const topBot = stats.top_performer;
                const winRate = typeof topBot.win_rate === 'number' 
                    ? topBot.win_rate.toFixed(1) 
                    : parseFloat(topBot.win_rate || 0).toFixed(1);
                document.getElementById('swarm-top-bot').textContent = 
                    `#${topBot.bot_id} (${winRate}%)`;
            }
            
            // تحديث متوسط الدقة
            if (stats.average_accuracy !== undefined) {
                document.getElementById('swarm-avg-accuracy').textContent = 
                    `${stats.average_accuracy.toFixed(1)}%`;
            }
            
            // تحديث تجارب ورقية
            if (stats.total_paper_trades !== undefined) {
                document.getElementById('swarm-paper-trades').textContent = 
                    stats.total_paper_trades;
            }
            
            // تحديث تصويتات اليوم
            if (stats.votes_today !== undefined) {
                document.getElementById('swarm-today-votes').textContent = 
                    stats.votes_today;
            }
            
            // تحديث القرار الحالي
            if (stats.latest_decision) {
                const voteValue = document.querySelector('#swarm-current-vote .vote-value');
                const decision = stats.latest_decision;
                
                if (decision === 'BUY') {
                    voteValue.textContent = 'شراء 🟢';
                    voteValue.className = 'vote-value buy';
                } else if (decision === 'SELL') {
                    voteValue.textContent = 'بيع 🔴';
                    voteValue.className = 'vote-value sell';
                } else {
                    voteValue.textContent = 'محايد';
                    voteValue.className = 'vote-value';
                }
            }
        } else {
            swarmContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('خطأ في تحديث بيانات السرب:', error);
    }
}

async function updateCausalData() {
    try {
        const response = await fetch('/causal-graph');
        const data = await response.json();
        
        const causalContainer = document.getElementById('causal-card-container');
        
        if (data.success && data.enabled) {
            causalContainer.style.display = 'block';
            
            const graph = data.graph;
            
            if (graph.total_nodes) {
                document.getElementById('causal-nodes').textContent = graph.total_nodes;
            }
            
            if (graph.total_edges) {
                document.getElementById('causal-edges').textContent = graph.total_edges;
            }
        } else {
            causalContainer.style.display = 'none';
        }
    } catch (error) {
        console.error('خطأ في تحديث بيانات التحليل السببي:', error);
    }
}
