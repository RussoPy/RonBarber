# RonBarber App 💈

A smart mobile scheduling app built for barbers.  
Designed for daily appointment management and client reminders via SMS.

---

## 📱 Features

### ✅ Authentication & Security
- Firebase Authentication (email & password)
- "Remember Me" with persistent login
- Auto-logout if user is deleted from Firebase
- Greeting message on login: "Hello, [name]"

### ✅ Appointment Management
- Add/edit/delete appointments
- Select contact from phonebook
- Assign custom time to each appointment
- View per-day schedule with real-time sync
- Duplicate appointment to the same time next week
- Lock appointment list after sending messages
- Unlock button with warning
- Highlight appointments that were already sent (colored green)

### ✅ Messaging
- Twilio SMS integration (paid account)
- Send bulk messages per day
- Auto-format Israeli phone numbers (+972)
- Visual progress bar: `X / Y messages sent`
- Each appointment stores: sent status, timestamp, Twilio SID
- Fallback: Manual "Send SMS" button per client
- Red warning prompt when trying to resend on same day

### ✅ Admin & Analytics
- Firebase usage tracking per user
- View total messages sent per user and per day

---

## 🧪 Coming Soon

### 💬 Custom Message Templates
- Each user can define their own SMS message format

### 💳 Paywall & Subscription
- Only paid users can use the "Send Messages" button
- Free users send messages manually
- Integrate PayPal or Stripe for $10/month
- Send invoice/receipt by email
- Admin-only override: mark any user as "paid"

### 🔄 Weekly Resets (optional)
- Option to reset all `sent: true` flags weekly

### 🧾 PDF Export (optional)
- Export schedule as a styled PDF per day

---

## 🛠️ Tech Stack

- React Native with Expo
- Firebase (Auth + Realtime Database)
- Twilio (SMS)
- Flask (Backend API for message triggers)
- Render.com (deployment)
