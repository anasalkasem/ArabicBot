# 🔐 Environment Variables Template
**For Railway Deployment - Binance Trading Bot**

---

## 📋 Quick Setup

Copy-paste this template into Railway **Variables** tab:

```bash
# ============================================
# BINANCE API KEYS - REQUIRED FOR TRADING
# ============================================
# Get from: https://www.binance.com/en/my/settings/api-management
# Permissions needed: Enable Reading + Enable Spot & Margin Trading
# Security: Disable Withdrawals!

BINANCE_API_KEY=
BINANCE_API_SECRET=


# ============================================
# BINANCE FUTURES API - FOR LONG/SHORT TRADING
# ============================================
# Create separate API key for Futures trading
# Permissions: Enable Reading + Enable Futures
# Test on Testnet first: https://testnet.binancefuture.com

BINANCE_FUTURES_API_KEY=
BINANCE_FUTURES_API_SECRET=


# ============================================
# TELEGRAM BOT - NOTIFICATIONS & CONTROL
# ============================================
# Get from: @BotFather on Telegram
# 1. Open Telegram → Search: @BotFather
# 2. Send: /newbot
# 3. Follow instructions → Get token
# 4. Get Chat ID: Send message to bot → Visit:
#    https://api.telegram.org/bot<TOKEN>/getUpdates
#    Copy "chat":{"id": YOUR_CHAT_ID}

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=


# ============================================
# OPENAI API - AI MARKET ANALYSIS (OPTIONAL)
# ============================================
# Get from: https://platform.openai.com/api-keys
# Used for: /analyze command, AI chat, market insights
# Model: GPT-4o-mini (fast & cheap)

OPENAI_API_KEY=


# ============================================
# SESSION SECRET - FLASK SECURITY
# ============================================
# Generate random string (64+ characters)
# Use: openssl rand -hex 32
# Or leave empty for auto-generation

SESSION_SECRET=


# ============================================
# SYSTEM VARIABLES - AUTO-SET BY RAILWAY
# ============================================
# DO NOT SET THESE MANUALLY - Railway auto-injects:
# - DATABASE_URL (from PostgreSQL service)
# - PORT (auto-assigned by Railway)
# - PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
```

---

## 🔑 Detailed Setup Instructions

### **1. Binance API Keys**

#### **For Spot Trading:**

1. **Login**: [binance.com](https://www.binance.com)
2. **Navigate**: Profile Icon → API Management
3. **Create API**: Click "Create API" → Label: "Railway Trading Bot"
4. **Configure**:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ **Disable Withdrawals** (Critical for security!)
5. **Copy Keys**: Save both API Key and Secret
6. **Paste**: Into Railway Variables tab

**Security Tips:**
- Create IP whitelist (get Railway IP from logs)
- Never commit keys to GitHub
- Use separate API for testing

#### **For Futures Trading (LONG/SHORT):**

1. **Same process as above**
2. **Additionally enable**: Futures trading permission
3. **Recommended**: Create **separate API key** for Futures
4. **Test first**: Use Binance Futures Testnet

**Testnet Setup:**
```bash
# Testnet API: https://testnet.binancefuture.com
# Get testnet API keys (separate from mainnet)
# In config.json:
{
  "testnet": true,
  "futures": {
    "testnet_enabled": true
  }
}
```

---

### **2. Telegram Bot Token**

#### **Step-by-Step:**

```bash
# 1. Open Telegram app
Open Telegram → Search: @BotFather

# 2. Create new bot
Send: /newbot
BotFather: Alright, a new bot. How are we going to call it?
You: My Trading Bot
BotFather: Good. Now let's choose a username for your bot.
You: my_trading_bot
BotFather: Done! Here is your token: 123456789:ABC-DEF...

# 3. Copy token
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF...
```

#### **Get Chat ID:**

```bash
# Method 1: Using Bot
1. Send message to your bot (any message)
2. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
3. Find: "chat":{"id": 987654321}
4. Copy: TELEGRAM_CHAT_ID=987654321

# Method 2: Using @userinfobot
1. Open Telegram → Search: @userinfobot
2. Send: /start
3. Bot replies with your ID
4. Use that as TELEGRAM_CHAT_ID
```

---

### **3. OpenAI API Key (Optional)**

#### **Get API Key:**

1. **Visit**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Login/Signup**: Using Google/GitHub
3. **Create Key**: Click "+ Create new secret key"
4. **Name it**: "Trading Bot - Railway"
5. **Copy**: Save immediately (shown only once!)

**Pricing** (as of Nov 2025):
- GPT-4o-mini: $0.15 per 1M input tokens
- Bot usage: ~$0.50-2/month (light usage)

**Features Enabled:**
- `/analyze` - AI market analysis
- `/audit` - Trading performance audit
- AI Chat - Intelligent assistant

**Optional**: Leave blank to disable AI features

---

### **4. Session Secret**

#### **Generate Secure Secret:**

**Option 1: Using OpenSSL (Recommended)**
```bash
# In terminal:
openssl rand -hex 32

# Output: a1b2c3d4e5f6...64_character_string
# Copy entire output → SESSION_SECRET=...
```

**Option 2: Using Python**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Option 3: Using Website**
- Visit: [randomkeygen.com](https://randomkeygen.com)
- Copy "CodeIgniter Encryption Keys"

**Option 4: Auto-Generation**
- Leave blank → Bot generates on first run
- Check logs for: `Generated SESSION_SECRET`

---

## ✅ Validation Checklist

### **Before Deploying:**

- [ ] All required variables filled (Binance API)
- [ ] API keys tested on Binance website
- [ ] Telegram bot responds to messages
- [ ] OpenAI API key valid (check: platform.openai.com/usage)
- [ ] No keys committed to Git
- [ ] IP whitelist configured on Binance

### **After Deploying:**

- [ ] Check `/health` endpoint returns healthy
- [ ] Check logs for: `✅ Binance client initialized`
- [ ] Send Telegram message → Bot responds
- [ ] Test `/analyze` command (if OpenAI enabled)
- [ ] No `HTTP 451` errors in logs

---

## 🔒 Security Best Practices

### **DO:**
✅ Store keys in Railway Variables only  
✅ Use IP whitelist on Binance  
✅ Disable withdrawals on API keys  
✅ Create separate keys for Testnet vs Live  
✅ Rotate keys periodically (every 90 days)  
✅ Use different API keys per environment  

### **DON'T:**
❌ Commit keys to Git  
❌ Share keys in Discord/Telegram  
❌ Use same key for multiple bots  
❌ Enable withdrawals on trading API  
❌ Store keys in code comments  
❌ Screenshot keys and upload  

---

## 🆘 Troubleshooting

### **"Invalid API Key" Error**

```bash
# Check:
1. API key copied correctly (no spaces)
2. API secret matches the key
3. API not deleted on Binance
4. Permissions enabled (Reading + Spot Trading)
5. IP whitelist includes Railway IP (if enabled)
```

### **"Telegram Bot Not Responding"**

```bash
# Check:
1. Token format: 123456789:ABC-DEF... (with colon)
2. Chat ID is number (not username)
3. Bot started (/start command sent)
4. Token not revoked by @BotFather
```

### **"OpenAI Rate Limit" Error**

```bash
# Solutions:
1. Add payment method: platform.openai.com/settings/billing
2. Upgrade tier: Tier 1 ($5 credit) sufficient
3. Or disable AI features: Remove OPENAI_API_KEY
```

---

## 📊 Example Configuration

### **Minimal Setup (Spot Trading Only):**
```bash
BINANCE_API_KEY=abc123...
BINANCE_API_SECRET=xyz789...
```

### **Standard Setup (With Notifications):**
```bash
BINANCE_API_KEY=abc123...
BINANCE_API_SECRET=xyz789...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321
SESSION_SECRET=a1b2c3d4e5f6...
```

### **Full Setup (Futures + AI):**
```bash
# Spot Trading
BINANCE_API_KEY=abc123...
BINANCE_API_SECRET=xyz789...

# Futures Trading
BINANCE_FUTURES_API_KEY=futures123...
BINANCE_FUTURES_API_SECRET=futures_secret...

# Notifications
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321

# AI Features
OPENAI_API_KEY=sk-proj-...

# Security
SESSION_SECRET=a1b2c3d4e5f6...
```

---

## 🔗 Useful Links

- **Binance API Docs**: [binance-docs.github.io/apidocs](https://binance-docs.github.io/apidocs)
- **Telegram Bot API**: [core.telegram.org/bots](https://core.telegram.org/bots)
- **OpenAI Platform**: [platform.openai.com](https://platform.openai.com)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)

---

*Last Updated: November 16, 2025*  
*Platform: Railway*  
*Bot Version: 2.0*
