# 🚂 دليل النشر على Railway

## الخطوات الكاملة لنقل البوت من Replit إلى Railway

---

## 📋 الخطوة 1: تحضير المشروع

✅ **تم بالفعل!** الملفات التالية جاهزة:
- `requirements.txt` - المكتبات المطلوبة
- `Procfile` - أمر التشغيل
- `railway.json` - إعدادات Railway
- `runtime.txt` - إصدار Python
- `.gitignore` - تحديث لإزالة ملفات Replit

---

## 📤 الخطوة 2: رفع الكود على GitHub

### 2.1 إنشاء Repository جديد على GitHub:

1. اذهب إلى [github.com](https://github.com)
2. اضغط **"New repository"** (الزر الأخضر)
3. أدخل اسم المشروع: `binance-trading-bot`
4. اجعله **Private** (خاص)
5. **لا تضيف** README أو .gitignore (موجودين)
6. اضغط **"Create repository"**

### 2.2 ربط المشروع بـ GitHub:

افتح **Shell** في Replit واكتب:

```bash
# 1. تهيئة Git (إذا لم يكن موجود)
git init

# 2. إضافة جميع الملفات
git add .

# 3. Commit الملفات
git commit -m "Initial commit - Ready for Railway deployment"

# 4. ربط الـ Repository (استبدل YOUR_USERNAME باسم حسابك)
git remote add origin https://github.com/YOUR_USERNAME/binance-trading-bot.git

# 5. رفع الكود
git branch -M main
git push -u origin main
```

**ملاحظة:** إذا طلب منك اسم المستخدم وكلمة المرور:
- استخدم **Personal Access Token** بدلاً من كلمة المرور
- احصل عليه من: Settings → Developer settings → Personal access tokens

---

## 🚀 الخطوة 3: النشر على Railway

### 3.1 إنشاء حساب على Railway:

1. اذهب إلى [railway.app](https://railway.app)
2. اضغط **"Login"**
3. سجّل دخول باستخدام **GitHub** (أسهل طريقة)
4. امنح Railway الصلاحيات المطلوبة

### 3.2 إنشاء مشروع جديد:

1. اضغط **"New Project"**
2. اختر **"Deploy from GitHub repo"**
3. ابحث عن `binance-trading-bot`
4. اضغط **"Deploy Now"**

### 3.3 اختيار المنطقة (مهم جداً!):

1. في صفحة المشروع، اذهب إلى **Settings**
2. ابحث عن **"Region"**
3. اختر **"Europe (eu-west-1)"** أو **"Singapore (ap-southeast-1)"**
4. احفظ التغييرات

---

## 🔐 الخطوة 4: إضافة API Keys

### في Railway:

1. اذهب إلى تبويب **"Variables"**
2. اضغط **"New Variable"**
3. أضف المتغيرات التالية:

```
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
SESSION_SECRET=any_random_string_here
```

**مهم:** 
- استخدم مفاتيح **Binance Testnet** للتجربة
- احصل عليها من: [testnet.binance.vision](https://testnet.binance.vision/)

---

## ✅ الخطوة 5: التحقق من التشغيل

### 5.1 مراقبة السجلات:

1. في Railway، اذهب إلى تبويب **"Deployments"**
2. اضغط على آخر deployment
3. شاهد الـ **Logs**
4. يجب أن ترى:
   ```
   🤖 Binance Trading Bot Starting...
   ✨ Multi-Timeframe Analysis: ENABLED
   ✨ Trailing Stop-Loss: ENABLED
   🚀 Bot is now running...
   ```

### 5.2 فتح الواجهة:

1. في الأعلى، ابحث عن **"Deployments"**
2. اضغط على الرابط (مثل: `your-bot.up.railway.app`)
3. يجب أن تفتح لوحة التحكم!

---

## 🌍 الخطوة 6: التأكد من عدم الحظر

### اختبار الاتصال بـ Binance:

في السجلات، يجب أن **لا** ترى:
```
❌ Binance API is geo-restricted
```

إذا رأيت هذا الخطأ:
1. تأكد أنك اخترت **Europe** أو **Asia** في الإعدادات
2. جرب منطقة أخرى: **Settings → Region**
3. أعد النشر: **Deployments → Redeploy**

---

## 🎯 الخطوة 7: التحول من Testnet إلى Live

**بعد التجربة الناجحة:**

1. احصل على API keys من [binance.com](https://www.binance.com)
2. في Railway Variables، غيّر:
   ```
   BINANCE_API_KEY=new_live_key
   BINANCE_API_SECRET=new_live_secret
   ```
3. في `config.json`، غيّر:
   ```json
   "testnet": false
   ```
4. Commit ورفع على GitHub:
   ```bash
   git add config.json
   git commit -m "Switch to live trading"
   git push
   ```
5. Railway سيعيد النشر تلقائياً!

---

## 📊 مراقبة البوت

### الواجهة المباشرة:
- **الصفحة الرئيسية:** `https://your-bot.up.railway.app/`
- **حالة البوت:** `https://your-bot.up.railway.app/status`
- **السجلات:** `https://your-bot.up.railway.app/logs`

### في Railway Dashboard:
- **Metrics:** استهلاك الذاكرة والمعالج
- **Logs:** السجلات المباشرة
- **Deployments:** تاريخ النشر

---

## 💰 التكلفة

Railway يوفر:
- **$5 مجاناً** كل شهر
- **Pay-as-you-go** بعد ذلك
- متوسط تكلفة البوت: **$3-7/شهر**

---

## 🔧 استكشاف الأخطاء

### البوت لا يعمل:
```bash
# في Logs، ابحث عن الأخطاء
# الأسباب الشائعة:
- Missing dependencies → تحقق من requirements.txt
- API keys خاطئة → راجع Variables
- Port مشغول → تأكد من استخدام PORT variable
```

### الواجهة لا تفتح:
```bash
# تأكد من:
1. Flask يعمل على 0.0.0.0
2. PORT variable معرّف
3. Templates و Static folders موجودة
```

### Binance محظور:
```bash
# الحل:
1. غيّر Region في Railway
2. جرب: Europe, Singapore, Japan
3. تجنب: US regions
```

---

## 📞 الدعم

**مشكلة في Railway:**
- [Railway Docs](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)

**مشكلة في البوت:**
- راجع `bot.log` في السجلات
- تحقق من الإعدادات في `config.json`

---

## 🎉 تم بنجاح!

البوت الآن:
- ✅ يعمل 24/7 على Railway
- ✅ في منطقة غير محظورة
- ✅ مع واجهة مراقبة جميلة
- ✅ Trailing stop-loss + Multi-timeframe analysis

**استمتع بالتداول الآلي! 🚀**
