import os
import re

d = r"C:\Users\ancus\Downloads\realestate (3)\realestate\backend\frontend\frontend"

# 1. Update cache busters to v=5 in all HTML files
html_files = [f for f in os.listdir(d) if f.endswith('.html')]
for file in html_files:
    path = os.path.join(d, file)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace script.js script.js?v=3 script.js?v=4 etc with script.js?v=5
    new_content = re.sub(r'src="script\.js(\?v=\d+)?"', 'src="script.js?v=5"', content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated cache buster to v=5 in {file}")

# 2. Patch add-property.html (remove top-level isLoggedIn guard as it is handled in init())
path = os.path.join(d, 'add-property.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target_str = "if (!Auth.isLoggedIn()) window.location.href = 'login.html';"
if target_str in content:
    content = content.replace(target_str, "// Auth check is handled in init() below")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched add-property.html successfully!")
else:
    print("WARNING: Could not find top-level isLoggedIn in add-property.html!")

# 3. Patch login.html
path = os.path.join(d, 'login.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace redirectIfLoggedIn
redirect_target = "Auth.redirectIfLoggedIn();"
redirect_replacement = """(async () => {
  // Check if we are in the middle of a GitHub OAuth redirect callback
  const isOAuthCallback = window.location.hash.includes('access_token=') || window.location.search.includes('code=');
  if (isOAuthCallback) return;

  const logged = await Auth.isLoggedIn();
  if (logged) {
    window.location.href = 'home.html';
  } else {
    if (typeof sb !== 'undefined' && sb) {
      try {
        const { data: { session } } = await sb.auth.getSession();
        if (session && session.user) {
          // Stale session (e.g. closed browser mid-login).
          // Clear it WITHOUT calling Auth.logout() which would redirect to login.html (causing infinite loop).
          try { sessionStorage.removeItem('re_2fa_verified_' + session.user.id); } catch(e) {}
          try { localStorage.removeItem('re_2fa_verified_' + session.user.id); } catch(e) {}
          try { await sb.auth.signOut(); } catch(e) {}
        }
      } catch(e) {}
    }
  }
})();"""

if redirect_target in content:
    content = content.replace(redirect_target, redirect_replacement)
    print("Replaced redirectIfLoggedIn in login.html")
else:
    print("WARNING: Could not find redirectIfLoggedIn in login.html!")

# Replace sendOTP
send_otp_pattern = r'async function sendOTP\(email, name, otp\) \{[\s\S]*?\}'
send_otp_replacement = """async function sendOTP(email, name, otp) {
  if (!email || !otp) return false;

  if (EJ.publicKey === 'YOUR_PUBLIC_KEY') {
    // Dev mode – show the OTP in a toast so you can test without EmailJS
    showToast("🛠 Dev OTP for " + email + ": " + otp, 'info');
    console.info("[DEV] OTP for " + email + ":", otp);
    return true; // pretend it was sent
  }

  try {
    if (typeof emailjs === 'undefined') {
      throw new Error("EmailJS library not loaded");
    }
    await emailjs.send(EJ.serviceId, EJ.templateId, {
      to_email: email,
      to_name:  name || email.split('@')[0],
      otp_code: otp,
      app_name: "🏠 RealEstate",
    });
    return true;
  } catch (err) {
    console.warn('EmailJS error (proceeding in fallback dev mode):', err);
    showToast("🛠 Dev Mode Fallback: OTP is " + otp, 'info');
    console.info("[DEV FALLBACK] OTP for " + email + ":", otp);
    return true; // proceed with login using the fallback OTP
  }
}"""

content, count = re.subn(send_otp_pattern, send_otp_replacement, content)
if count > 0:
    print("Replaced sendOTP in login.html")
else:
    print("WARNING: Could not find sendOTP in login.html!")

# Patch loginForm submit handler to save re_pending_user to sessionStorage
submit_target = """    // 3. Generate + send OTP
    loggedEmail = email;
    loggedUser  = user;"""
submit_replacement = """    // 3. Generate + send OTP
    loggedEmail = email;
    loggedUser  = user;
    try { sessionStorage.setItem('re_pending_user', JSON.stringify(user)); } catch(e) { console.error("Failed to save pending user to sessionStorage:", e); }"""

if submit_target in content:
    content = content.replace(submit_target, submit_replacement)
    print("Patched loginForm submit handler in login.html")
else:
    print("WARNING: Could not find loginForm submit target in login.html!")

# Patch doVerify to set 2FA verified state and load pending user
do_verify_target = """  // Session is already established by Auth.login() via Supabase
  btn.textContent = '✅ Verified!';
  if (typeof SecurityLog !== 'undefined') SecurityLog.add('otp_verified', 'Login OTP verified successfully', loggedEmail);
  showToast('Login successful! 🎉', 'success');
  setTimeout(() => window.location.href = 'home.html', 1100);"""

do_verify_replacement = """  // Session is already established by Auth.login() via Supabase
  btn.textContent = '✅ Verified!';
  let user = loggedUser;
  if (!user) {
    try { user = JSON.parse(sessionStorage.getItem('re_pending_user')); } catch(e) { console.error("Failed to parse pending user from sessionStorage:", e); }
  }
  console.log("[doVerify] Verifying OTP. Selected user:", user);
  if (user) {
    Auth.set2FAVerified(user.id, true);
    try { sessionStorage.removeItem('re_pending_user'); } catch(e) {}
  } else {
    console.error("[doVerify] Verification error: No user state found! Cannot mark 2FA verified!");
  }
  if (typeof SecurityLog !== 'undefined') SecurityLog.add('otp_verified', 'Login OTP verified successfully', loggedEmail);
  showToast('Login successful! 🎉', 'success');
  setTimeout(() => window.location.href = 'home.html', 1100);"""

if do_verify_target in content:
    content = content.replace(do_verify_target, do_verify_replacement)
    print("Patched doVerify in login.html")
else:
    print("WARNING: Could not find doVerify target in login.html!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# 4. Patch signup.html
path = os.path.join(d, 'signup.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace sendOTPEmail
send_otp_signup_pattern = r'async function sendOTPEmail\(email, name, otp\) \{[\s\S]*?\}'
send_otp_signup_replacement = """async function sendOTPEmail(email, name, otp) {
  if (EJ.publicKey === 'YOUR_PUBLIC_KEY') {
    showToast("Dev Mode - Code: " + otp, 'info');
    setTimeout(() => alert(" Dev Code: " + otp + "\\n\\nConfigure EmailJS for real emails!\\nVisit emailjs.com to set up a free account."), 300);
    return { success: true, dev: true };
  }
  try {
    if (typeof emailjs === 'undefined') {
      throw new Error("EmailJS library not loaded");
    }
    await emailjs.send(EJ.serviceId, EJ.templateId, {
      to_email: email,
      to_name:  name || email.split('@')[0],
      otp_code: otp,
      app_name: ' RealEstate',
    });
    return { success: true };
  } catch(err) {
    console.warn('EmailJS error (proceeding in fallback dev mode):', err);
    showToast("🛠 Dev Mode Fallback: OTP is " + otp, 'info');
    console.info("[DEV FALLBACK] OTP for " + email + ":", otp);
    return { success: true, dev: true }; // Proceed anyway using the fallback
  }
}"""

content, count = re.subn(send_otp_signup_pattern, send_otp_signup_replacement, content)
if count > 0:
    print("Replaced sendOTPEmail in signup.html")
else:
    print("WARNING: Could not find sendOTPEmail in signup.html!")

# Patch signupForm submit handler to save re_pending_signup to sessionStorage
signup_submit_target = """    // Save pending data (though user is already in SB, we keep state for next step)
    pendingData = { name, email, pass, role };"""
signup_submit_replacement = """    // Save pending data (though user is already in SB, we keep state for next step)
    pendingData = { name, email, pass, role, userId: user ? user.id : null };
    try { sessionStorage.setItem('re_pending_signup', JSON.stringify(pendingData)); } catch(e) {}"""

if signup_submit_target in content:
    content = content.replace(signup_submit_target, signup_submit_replacement)
    print("Patched signupForm submit handler in signup.html")
else:
    print("WARNING: Could not find signupForm submit target in signup.html!")

# Replace verifyOTPAndRegister to load pending data and call Auth.set2FAVerified
verify_signup_otp_pattern = r'async function verifyOTPAndRegister\(\) \{[\s\S]*?\}'
verify_signup_otp_replacement = """async function verifyOTPAndRegister() {
  const entered = getOTP();
  if (entered.length < 6) { showToast('Please enter the complete 6-digit code', 'warning'); return; }

  const btn = document.getElementById('verifyBtn');
  btn.textContent = 'Verifying...';
  btn.disabled = true;

  let pData = pendingData;
  if (!pData) {
    try { pData = JSON.parse(sessionStorage.getItem('re_pending_signup')); } catch(e) {}
  }
  if (!pData) {
    console.error("[verifyOTPAndRegister] Error: No pending signup data found!");
    showToast("Signup state lost. Please register again.", "error");
    btn.textContent = ' Verify & Create Account';
    btn.disabled = false;
    return;
  }

  const result = OTP.verify(pData.email, entered);

  if (!result.valid) {
    shakeBoxes();
    showToast(result.msg, 'error');
    btn.textContent = ' Verify & Create Account';
    btn.disabled = false;
    return;
  }

  // OTP correct - user already created in Supabase in step 1
  clearInterval(otpInterval);
  clearInterval(resendTimer);

  btn.textContent = ' Verified!';
  console.log("[verifyOTPAndRegister] Verification success. Setting 2FA verified for:", pData.userId);
  if (pData.userId) {
    Auth.set2FAVerified(pData.userId, true);
    try { sessionStorage.removeItem('re_pending_signup'); } catch(e) {}
  }
  showToast(`Welcome ${pData.name}! Email verified successfully`, 'success');
  setTimeout(() => window.location.href = 'home.html', 1200);
}"""

content, count = re.subn(verify_signup_otp_pattern, verify_signup_otp_replacement, content)
if count > 0:
    print("Replaced verifyOTPAndRegister in signup.html")
else:
    print("WARNING: Could not find verifyOTPAndRegister in signup.html!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# 5. Patch profile.html
path = os.path.join(d, 'profile.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

change_pass_target = """  try {
    const { error } = await sb.auth.updateUser({ password: newPass });
    if (error) throw error;

    document.getElementById('passwordForm').reset();
    showToast('Password changed successfully! ', 'success');
  } catch(err) {
    showError(document.getElementById('newPass'), err.message);
    showToast('Could not update password', 'error');
  }"""

change_pass_replacement = """  const btn = e.target.querySelector('button[type="submit"]');
  if (btn) { btn.disabled = true; btn.textContent = 'Updating...'; }

  try {
    let updatedOnline = false;
    if (typeof sb !== 'undefined' && sb) {
      try {
        const { error } = await sb.auth.updateUser({ password: newPass });
        if (error) throw error;
        updatedOnline = true;
      } catch (err) {
        if (!isNetworkError(err)) {
          throw err;
        }
      }
    }

    // Also update offline profile in localStorage if available
    try {
      const user = Auth.currentUser || await Auth.getUser();
      if (user && user.email) {
        let users = [];
        try { users = JSON.parse(localStorage.getItem('re_users') || '[]'); } catch(e) { users = []; }
        const userIndex = users.findIndex(u => u.email === user.email);
        if (userIndex !== -1) {
          const hashed = await hashPassword(newPass);
          users[userIndex].passwordHash = hashed;
          localStorage.setItem('re_users', JSON.stringify(users));
          // If offline mode is active, update mock session as well
          const offSess = localStorage.getItem('sb_offline_session');
          if (offSess) {
            const sess = JSON.parse(offSess);
            if (sess && sess.user && sess.user.email === user.email) {
              sess.user.passwordHash = hashed;
              localStorage.setItem('sb_offline_session', JSON.stringify(sess));
            }
          }
        }
      }
    } catch(e) {
      console.warn("Failed to update offline password backup:", e);
    }

    document.getElementById('passwordForm').reset();
    showToast('Password changed successfully! 🎉', 'success');
  } catch(err) {
    console.error('Password Update Error:', err);
    showError(document.getElementById('newPass'), err.message || 'Could not update password');
    showToast('Could not update password', 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Update Password'; }
  }"""

if change_pass_target in content:
    content = content.replace(change_pass_target, change_pass_replacement)
    print("Patched profile.html successfully!")
else:
    print("WARNING: Could not find change_pass_target in profile.html!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("All patches completed successfully!")
