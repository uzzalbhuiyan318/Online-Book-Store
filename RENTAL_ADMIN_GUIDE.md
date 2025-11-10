# 📚 Book Rental System - Complete Admin Guide

## ✅ FIXED: Maximum Rental Limit

### Previous Issue
- Default was 5 active rentals per user
- Users could rent too many books at once

### ✅ Solution Applied
- **Changed default to 3 active rentals per user**
- Users must return at least one book to rent more
- Prevents abuse and ensures book availability

---

## 🎯 Rental Settings Explained

### Location
**Admin Panel → Rentals → Rental Settings**

### Settings Overview

#### 💰 **Pricing Settings**

| Setting | Default | Description |
|---------|---------|-------------|
| **Security Deposit Percentage** | 20% | Percentage of book price held as deposit (refundable on timely return) |
| **Daily Late Fee** | ৳10 | Amount charged per day for overdue rentals |

**Example:**
- Book price: ৳500
- Security deposit: ৳100 (20% of ৳500)
- Rental fee (14-day plan at 15%): ৳75
- **Total payment:** ৳175
- **Refund on return:** ৳100 (security deposit)

---

#### 📊 **Rental Limits** (IMPORTANT!)

| Setting | Recommended | Description |
|---------|-------------|-------------|
| **Max Active Rentals Per User** | **3** | Maximum books one user can rent simultaneously |
| **Max Renewals** | 3 | How many times a rental can be extended |
| **Min Stock for Rental** | 1 | Minimum stock required to allow rental |

**How Max Active Rentals Works:**

```
User has 3 active rentals (LIMIT REACHED)
         ↓
Cannot rent more books
         ↓
Must return at least 1 book
         ↓
Can rent again (now has 2 active)
```

**Real-World Scenario:**
1. ✅ User rents Book A, B, C (3/3 active) ← **AT LIMIT**
2. ❌ Tries to rent Book D → **BLOCKED** ("You have reached maximum limit")
3. ✅ Returns Book A (2/3 active)
4. ✅ Can now rent Book D (3/3 active again)

---

#### 🔔 **Notification Settings**

| Setting | Default | Description |
|---------|---------|-------------|
| **Enable Notifications** | Yes | Turn rental notifications on/off |
| **Due Soon Days** | 3 | Send reminder X days before due date |

**Notification Types:**
1. 🎉 **Rental Confirmed** - When admin activates rental
2. ✓ **Rental Active** - When rental period starts
3. ⏰ **Due Soon** - 3 days before due date
4. ⚠️ **Due Tomorrow** - 1 day before due date
5. 🚨 **Overdue** - When book is not returned on time
6. ✅ **Returned** - When book is successfully returned
7. 🔄 **Renewal Confirmed** - When rental is extended
8. ⭐ **Feedback Request** - After successful return

---

## 🛠️ Admin Panel Features

### 1. **BookRental Management**

#### New Features Added:

**📊 User Active Rentals Column**
- Shows current active rentals count with color coding:
  - 🟢 **Green (✓):** Safe (e.g., 1/3)
  - 🟠 **Orange (⚡):** Near limit (e.g., 2/3)
  - 🔴 **Red (⚠️):** At limit (e.g., 3/3)

**📋 User Rental Summary**
- Displays complete user rental statistics:
  - Active rentals
  - Pending rentals
  - Overdue rentals
  - Total rentals
  - Warns when user is at maximum limit

**🔍 Enhanced Filtering**
- Filter by status (Active, Pending, Returned, Overdue, Cancelled)
- Filter by payment status
- Filter by date range (start date, due date, created date)
- Filter by renewal status

**🔔 New Bulk Actions**
1. **Send Due Reminder** - Notify users about upcoming due dates
2. **Send Overdue Notice** - Alert users about overdue books
3. **Calculate Late Fees** - Calculate fees for overdue rentals
4. **Mark as Active/Returned/Cancelled** - Bulk status updates

---

### 2. **Rental Notifications Management**

#### Enhanced Features:

**🎨 Color-Coded Notification Types**
- Each type has distinct color for quick identification
- Visual badges make it easy to scan notifications

**📊 Better Status Display**
- ✓ Read (Green checkmark)
- ● Unread (Orange dot with bold text)

**🗑️ Bulk Actions**
1. **Mark as Read/Unread** - Manage notification status
2. **Mark as Sent** - Track sent notifications
3. **Delete Read Notifications** - Clean up old notifications

**🔍 Advanced Search**
- Search by user email or name
- Search by notification title or message
- Search by rental number
- Filter by date range

---

### 3. **Rental Settings Dashboard**

#### New Statistics Display:

Shows real-time rental metrics:
- ✓ **Active Rentals:** Total currently active
- ⚠️ **Overdue:** Books not returned on time
- ⏳ **Pending:** Rentals waiting for activation
- 👥 **Users at Max Limit:** Users who can't rent more

**Visual Design:**
- Clear, colorful information box
- Real-time data
- Helps make informed decisions

---

## 📋 Admin Workflow Examples

### Scenario 1: User Wants to Rent but Can't

**Problem:** User complains they can't rent a book

**Admin Actions:**
1. Go to **Rentals → Book Rentals**
2. Search for user's email
3. Check **User Active Rentals** column
4. If showing "⚠️ 3/3":
   - User is at maximum limit
   - They must return a book first
5. Check for overdue rentals:
   - If overdue exists, send overdue notice
   - Calculate late fees if needed

---

### Scenario 2: Sending Due Date Reminders

**Admin Actions:**
1. Go to **Rentals → Book Rentals**
2. Filter by: **Status = Active**
3. Look for rentals with 3 days or less remaining
4. Select those rentals
5. Choose action: **"Send due date reminder notifications"**
6. Click **"Go"**
7. Users receive notification

---

### Scenario 3: Handling Overdue Rentals

**Admin Actions:**
1. Go to **Rentals → Book Rentals**
2. Look for **Red "Overdue by X days"** in Days Info column
3. Select overdue rentals
4. Choose action: **"Calculate late fees"**
5. Then choose: **"Send overdue notices"**
6. Users notified with late fee amount
7. Follow up manually if needed

---

### Scenario 4: Activating Pending Rentals

**Admin Actions:**
1. Go to **Rentals → Book Rentals**
2. Filter by: **Status = Pending**
3. Select rentals to activate
4. Choose action: **"Mark selected rentals as Active"**
5. Click **"Go"**
6. System automatically:
   - Sets status to Active
   - Sets start date to now
   - Creates activation notification

---

## 🔐 User Rental Limit Enforcement

### How It Works:

**Frontend (Book Rental Page):**
```python
# Check user's active rentals
active_rentals_count = BookRental.objects.filter(
    user=request.user,
    status='active'
).count()

# Compare with max allowed
if active_rentals_count >= settings.max_active_rentals_per_user:
    # Block rental
    messages.error(request, 'You have reached the maximum limit of 3 active rentals.')
```

**Backend Validation:**
```python
# Double-check on rental creation
if active_rentals_count >= settings.max_active_rentals_per_user:
    return redirect with error
```

**Admin View:**
- Admin can see exact count (e.g., "⚠️ 3/3")
- Warning displayed in rental summary
- Clear visual indicators

---

## 📊 Statistics & Reporting

### Available in Settings Dashboard:

1. **Active Rentals Count**
   - Total books currently rented
   - Helps track demand

2. **Overdue Count**
   - Books not returned on time
   - Requires follow-up action

3. **Pending Count**
   - Rentals waiting for activation
   - Admin needs to process

4. **Users at Max Limit**
   - Users who can't rent more
   - May need to send reminders

---

## 🎯 Best Practices for Admin

### Daily Tasks:
1. ✅ Check **Overdue Rentals** (send notices if needed)
2. ✅ Activate **Pending Rentals**
3. ✅ Review **Users at Max Limit** (check if they need reminders)

### Weekly Tasks:
1. ✅ Send **Due Date Reminders** (for rentals due in 3 days)
2. ✅ Calculate **Late Fees** for overdue rentals
3. ✅ Review **Rental Statistics** in Settings

### Monthly Tasks:
1. ✅ Clean up **Read Notifications** (delete old ones)
2. ✅ Review and approve **Feedback**
3. ✅ Analyze **Rental Patterns** (most rented books, frequent users)

---

## 🔧 Troubleshooting

### Issue: User Says They Can't Rent

**Check:**
1. Active rentals count (must be < 3)
2. Book stock availability
3. User account status
4. Any pending payments

---

### Issue: Notifications Not Sending

**Check:**
1. Settings → **Enable Notifications** = Yes
2. User has valid email
3. Notification was created in database
4. Check **is_sent** status

---

### Issue: Late Fees Not Calculating

**Check:**
1. Rental status = Active
2. Due date has passed
3. Run bulk action: **"Calculate late fees"**
4. Check **late_fee** field in rental

---

## 📱 User Experience Impact

### Before Fix:
- ❌ Users could rent 5 books at once
- ❌ Limited book availability
- ❌ Harder to manage returns

### After Fix:
- ✅ Maximum 3 books per user
- ✅ Better book availability
- ✅ Easier return management
- ✅ Fair distribution of books

---

## 🎉 Summary

### What Was Changed:

1. ✅ **Max Active Rentals:** 5 → 3
2. ✅ **Admin Panel:** Added user rental count with color coding
3. ✅ **Admin Panel:** Added complete user rental summary
4. ✅ **Admin Panel:** Added bulk notification sending
5. ✅ **Admin Panel:** Added real-time statistics
6. ✅ **Notifications:** Enhanced with color coding and better filters
7. ✅ **Settings:** Added visual statistics dashboard

### Benefits:

- **Better Control:** Admin can see exactly how many books each user has
- **Fair Distribution:** Max 3 books prevents hoarding
- **Easy Management:** Color-coded visuals make monitoring easy
- **Proactive Communication:** Bulk notification actions
- **Data-Driven:** Real-time statistics for decision making

---

## 🚀 Next Steps

1. **Test the limit:** Try renting 3 books as a user
2. **Check admin:** View the new active rentals column
3. **Send notifications:** Use bulk actions to notify users
4. **Monitor stats:** Check the statistics in Settings
5. **Adjust if needed:** Change max limit in Settings if required

**The rental system is now optimized for better book management and user experience!** 🎉
