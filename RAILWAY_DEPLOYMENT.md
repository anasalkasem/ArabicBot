# 🚀 Railway Deployment Guide - Binance Trading Bot
### **Professional Production Deployment with Futures Trading Support**

---

## 📋 Quick Navigation
1. [Quick Start (5 Minutes)](#-quick-start-5-minutes)
2. [Complete Setup Guide](#-complete-deployment-guide)
3. [Environment Variables](#-environment-variables-setup)
4. [Monitoring & Troubleshooting](#-monitoring--health-checks)
5. [Migration from Replit](#-migration-from-replit)

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites
- ✅ Railway Account ([railway.app](https://railway.app))
- ✅ GitHub Repository
- ✅ Binance API Keys ([Get them here](https://www.binance.com/en/my/settings/api-management))

### Deploy in 3 Steps

#### **Step 1: Connect GitHub Repository**
```bash
1. Login to Railway → railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select: binance-trading-bot repository
4. Branch: main
```

#### **Step 2: Add PostgreSQL Database**
```bash
1. In your project → Click "+ New"
2. Select "Database" → "PostgreSQL"
3. Wait 2-3 minutes for initialization
4. DATABASE_URL is auto-created ✅
```

#### **Step 3: Add Environment Variables**
```bash
Go to: Variables tab → Add these:

# Essential (Required for Trading)
BINANCE_API_KEY=your_spot_api_key_here
BINANCE_API_SECRET=your_spot_secret_here

# Futures Trading (For LONG/SHORT)
BINANCE_FUTURES_API_KEY=your_futures_api_key
BINANCE_FUTURES_API_SECRET=your_futures_secret

# Optional but Recommended
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
OPENAI_API_KEY=your_openai_key
```

**Click "Deploy"** → Wait 3-5 minutes → **Done! 🎉**

Your bot will be live at: `https://your-project.up.railway.app`

---

## 📖 Complete Deployment Guide

### 🔐 Getting Binance API Keys

#### **For Spot Trading:**

1. **Login to Binance** → [binance.com](https://www.binance.com)
2. **Profile** → **API Management**
3. **Create API** → Name: "Railway Trading Bot"
4. **Enable Permissions**:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ **Disable Withdrawals** (Security!)
5. **Save Keys** → Store safely

#### **For Futures Trading (LONG/SHORT):**

1. **Same as above**, but also:
2. **Enable Futures** permission
3. **Create separate API** (recommended for security)
4. **Test on Testnet first**:
   - Testnet: [testnet.binancefuture.com](https://testnet.binancefuture.com)

#### **Security Best Practices:**

✅ **IP Whitelist** (Highly Recommended):
```bash
# Get Railway IP from deployment logs
# Add to Binance API restrictions:
API Management → Edit API → Restrict access to trusted IPs
```

✅ **Separate API Keys**:
- Spot API for regular trading
- Futures API for leveraged positions
- Never share keys or commit to Git!

---

### 🗄️ Database Setup

#### **Automatic Configuration**

Railway PostgreSQL service handles everything:

1. ✅ **Creates Database Instance**
2. ✅ **Generates `DATABASE_URL`** (Format: `postgresql://user:pass@host:port/db`)
3. ✅ **Injects into Application** (No manual config!)
4. ✅ **Auto-Creates Tables** on first run:
   - `trades` - Trade history
   - `positions` - Open positions
   - `indicator_signals` - Strategy data
   - `indicator_outcomes` - Performance tracking
   - `daily_stats` - Daily metrics
   - `pair_stats` - Per-symbol stats
   - `market_regime_history` - Market conditions

#### **Database Management**

**Check Database Status:**
```bash
# In Railway Console:
railway run python -c "from db_manager import DatabaseManager; db = DatabaseManager(); print('✅ Connected')"
```

**Reset Database (if needed):**
```bash
# WARNING: Deletes all data!
railway run python -c "from db_manager import DatabaseManager; db = DatabaseManager(); db.reset_database()"
```

**Backup Database** (Railway Pro):
- Settings → Backups → Enable
- Daily automated backups
- 7-day retention

---

### 🔧 Environment Variables Setup

#### **Complete Variables List**

Go to: **Project → Bot Service → Variables**

```bash
# ============================================
# BINANCE API - REQUIRED FOR REAL TRADING
# ============================================
BINANCE_API_KEY=abc123xyz...
BINANCE_API_SECRET=secret456...

# Futures API (For LONG/SHORT positions)
BINANCE_FUTURES_API_KEY=futures_key...
BINANCE_FUTURES_API_SECRET=futures_secret...

# ============================================
# TELEGRAM NOTIFICATIONS - RECOMMENDED
# ============================================
# Get from: @BotFather on Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321

# ============================================
# OPENAI AI FEATURES - OPTIONAL
# ============================================
# Get from: platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...

# ============================================
# SECURITY - AUTO-GENERATED IF NOT SET
# ============================================
SESSION_SECRET=random_64_char_string_here

# ============================================
# SYSTEM - AUTO-SET BY RAILWAY
# ============================================
# These are injected by Railway - DO NOT SET MANUALLY:
# - DATABASE_URL (from PostgreSQL service)
# - PORT (auto-assigned by Railway)
```

#### **How to Get Telegram Bot Token**

```bash
1. Open Telegram → Search: @BotFather
2. Send: /newbot
3. Follow instructions → Choose name
4. Copy token (looks like: 123456:ABC-DEF...)

# Get Chat ID:
5. Send message to your bot
6. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates
7. Copy "chat":{"id": YOUR_CHAT_ID}
```

---

### 📊 Monitoring & Health Checks

#### **Railway Health Check**

URL: `https://your-app.up.railway.app/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "bot_status": "running",
  "iterations": 42,
  "uptime": "Started at 2025-11-16T03:00:00",
  "last_check": "2025-11-16T03:10:45"
}
```

#### **Monitoring Endpoints**

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/health` | Health check | System status |
| `/status` | Bot status + positions | Trading data |
| `/statistics` | Performance metrics | Win rate, P/L |
| `/logs` | Recent logs | Last 50 entries |

#### **Railway Metrics**

Access in **Project → Metrics** tab:

- 📈 **CPU Usage** (Should be <50%)
- 📊 **Memory Usage** (Should be <300MB)
- 🌐 **Network I/O**
- 📡 **Request Rate**

#### **Set Up Alerts**

```bash
Settings → Notifications → Add:
- 🔴 Deployment failures
- 🟡 CPU >80%
- 🟡 Memory >500MB
- 🔴 Health check failures
```

---

### 🔧 Troubleshooting

#### **Issue 1: Deployment Failed**

**Symptoms:**
```
❌ Build failed with error
❌ Dependencies not installed
```

**Solutions:**
```bash
1. Check build logs: Deployments tab → Latest build
2. Verify Python version: runtime.txt = python-3.12
3. Update dependencies: pip list (check for conflicts)
4. Rebuild: Settings → Redeploy
```

#### **Issue 2: Database Connection Error**

**Symptoms:**
```
❌ Error connecting to PostgreSQL
❌ DATABASE_URL not found
```

**Solutions:**
```bash
1. Verify PostgreSQL service exists:
   Dashboard → Should see PostgreSQL service

2. Check DATABASE_URL variable:
   Bot Service → Variables → Confirm DATABASE_URL exists

3. If missing, add PostgreSQL:
   + New → Database → PostgreSQL
   
4. Restart bot:
   Deployments → Redeploy
```

#### **Issue 3: Binance API Not Working**

**Symptoms:**
```
⚠️ Geo-restricted (HTTP 451)  ← Should NOT appear on Railway!
❌ Invalid API key
❌ IP not whitelisted
```

**Solutions:**
```bash
# This is the MAIN REASON we migrated to Railway!
# Railway does NOT have geo-restrictions ✅

1. Verify API keys are correct:
   Variables tab → Check BINANCE_API_KEY

2. Check API key permissions on Binance:
   - Enable Reading ✅
   - Enable Spot Trading ✅
   - Enable Futures (if using) ✅

3. IP Whitelist issue:
   - Get Railway IP from logs
   - Add to Binance API restrictions
   - OR: Remove IP restriction (less secure)

4. Test API:
   Logs → Look for: "✅ Binance client initialized"
```

#### **Issue 4: Bot Running But Not Trading**

**Symptoms:**
```
✅ Bot running
✅ Market analysis working
❌ No trades executed
```

**Solutions:**
```bash
1. Check config.json:
   {
     "testnet": false,  ← Must be false for live trading
     "futures": {
       "enabled": true  ← Enable for LONG/SHORT
     }
   }

2. Verify API keys match mode:
   - Spot API → Spot trading
   - Futures API → LONG/SHORT

3. Check buy signals:
   Logs → "✅ BUY SIGNAL DETECTED"
   If signals appear but no trades:
   - RSI/Stochastic/BB conditions too strict
   - Not enough balance
   - API permissions missing

4. Review risk settings:
   config.json → risk_management → position_size
```

#### **Issue 5: High Memory Usage**

**Symptoms:**
```
⚠️ Memory >500MB
❌ Bot crashes
```

**Solutions:**
```bash
1. Reduce trading pairs:
   config.json → trading_pairs: ["BTCUSDT", "ETHUSDT"]
   (Instead of 10+ pairs)

2. Increase check interval:
   config.json → check_interval: 10 (default: 5)

3. Disable heavy features:
   - momentum_enabled: false
   - regime_enabled: false
   - AI features (if not needed)

4. Upgrade Railway plan:
   Settings → Upgrade (512MB → 8GB RAM)
```

---

### 🔄 Migration from Replit

#### **Why Migrate?**

| Feature | Replit | Railway |
|---------|--------|---------|
| **Binance API** | ❌ HTTP 451 (Geo-blocked) | ✅ Full access |
| **Real Trading** | ❌ Mock data only | ✅ Live trading |
| **Performance** | ⚠️ Shared CPU | ✅ Dedicated resources |
| **Uptime** | ⚠️ Sleeps after 1h | ✅ Always-on |
| **Database** | ✅ PostgreSQL | ✅ PostgreSQL |
| **Cost** | $20/month | $5-10/month |

#### **Migration Steps**

**1. Export from Replit:**
```bash
# Download these files:
- config.json (your settings)
- trading_stats.json (optional - if you want history)
- positions.json (optional)
```

**2. Deploy to Railway:**
Follow [Quick Start](#-quick-start-5-minutes)

**3. Upload Configuration:**
```bash
# Option A: Railway Console
Files tab → Upload → config.json

# Option B: GitHub
Commit config.json → Push to main → Auto-deploy
```

**4. Test on Testnet First:**
```json
// config.json
{
  "testnet": true,
  "futures": {
    "testnet_enabled": true
  }
}
```

Monitor for 24 hours → Verify trades → Switch to live

**5. Enable Live Trading:**
```json
{
  "testnet": false,
  "futures": {
    "testnet_enabled": false
  }
}
```

---

## ✅ Post-Deployment Checklist

### **Essential Checks**

- [ ] Health check returns `"status": "healthy"`
- [ ] `/status` shows connected database
- [ ] Logs show: `✅ Binance client initialized`
- [ ] No `HTTP 451` errors in logs
- [ ] Telegram notifications working (if enabled)
- [ ] Dashboard accessible

### **Security Checks**

- [ ] API keys in Railway Variables (not in code!)
- [ ] Withdrawals disabled on Binance API
- [ ] IP whitelist configured (recommended)
- [ ] SESSION_SECRET is random

### **Trading Checks**

- [ ] Tested on Testnet first
- [ ] config.json reviewed
- [ ] Risk management configured
- [ ] Stop-loss/Take-profit set

---

## 📞 Support & Resources

### **Documentation**
- **Railway**: [docs.railway.app](https://docs.railway.app)
- **Binance API**: [binance-docs.github.io](https://binance-docs.github.io/apidocs)
- **Bot Docs**: `replit.md` in this repo

### **Community**
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Binance Developers: [dev.binance.vision](https://dev.binance.vision)

### **Troubleshooting**
1. Check deployment logs
2. Review this guide's troubleshooting section
3. Search Railway Discord
4. Open GitHub issue

---

## 🎯 Next Steps

1. ✅ Deploy to Railway (5 minutes)
2. ✅ Add Binance API Keys
3. ✅ Test on Testnet (24 hours)
4. ✅ Monitor performance
5. ✅ Enable Live Trading

**Your bot is now production-ready! 🚀**

---

*Last Updated: November 16, 2025*  
*Bot Version: 2.0 - Futures Enabled*  
*Platform: Railway*
