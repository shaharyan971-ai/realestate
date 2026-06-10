/* ============================================
   REAL ESTATE APP - MAIN SCRIPT
   Supabase Edition
   Shared across all pages
   ============================================ */

// PWA Service Worker Registration - DISABLED
// The SW was caching stale files causing login to crash.
// Re-enable once the app is stable.
// if ('serviceWorker' in navigator) {
//   window.addEventListener('load', () => {
//     navigator.serviceWorker.register('./sw.js').catch(err => {
//       console.warn('Service Worker registration failed:', err);
//     });
//   });
// }

// ============================================
// SUPABASE CLIENT INITIALIZATION
// ============================================
// SB_URL and SB_KEY are provided in config.js
let sb = null;

function checkSupabaseConfig() {
  if (typeof SB_URL === 'undefined' || typeof SB_KEY === 'undefined') return false;
  const isPlaceholder = SB_URL.includes('YOUR_SUPABASE_URL') || SB_KEY.includes('YOUR_SUPABASE_ANON_KEY');
  if (isPlaceholder) {
    console.warn("Supabase Setup Required: Please update config.js with your project values.");
    return false;
  }
  return true;
}

try {
  if (typeof supabase !== 'undefined' && checkSupabaseConfig()) {
    sb = supabase.createClient(SB_URL, SB_KEY);
  } else {
    if (typeof supabase !== 'undefined' && !checkSupabaseConfig()) {
      window.addEventListener('DOMContentLoaded', showSetupBanner);
    } else {
      console.warn("Supabase library not loaded. Using offline mode.");
    }
  }
} catch (e) {
  console.error("Supabase Init Error:", e);
}

function showSetupBanner() {
  const banner = document.createElement('div');
  banner.style.cssText = 'background:#8b4000;color:#fff;padding:12px;text-align:center;font-size:0.85rem;position:sticky;top:0;z-index:9999;cursor:pointer;font-weight:700;box-shadow:0 4px 10px rgba(0,0,0,0.3);';
  banner.innerHTML = '🛠️ Database Setup Required - Click for instructions on how to connect your Supabase project';
  banner.onclick = showSetupModal;
  document.body.prepend(banner);
}

function showSetupModal() {
  const modal = document.createElement('div');
  modal.className = "fixed inset-0 z-[10000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4";
  modal.innerHTML = `
    <div class="relative w-full max-w-lg rounded-xl border border-border bg-card text-card-foreground p-8 shadow-xl">
      <h2 class="text-xl font-bold tracking-tight text-foreground mb-4">Database Setup Required</h2>
      <p class="text-sm text-muted-foreground leading-relaxed mb-6">
        To enable login, data persistence, and listings, you need to connect your own <strong class="text-foreground">Supabase Project</strong>.
      </p>
      <div class="bg-muted/50 rounded-lg p-4 mb-6 text-xs text-muted-foreground space-y-2 border border-border">
        <p><strong>1.</strong> Sign up at <a href="https://supabase.com" target="_blank" class="text-primary underline underline-offset-2">supabase.com</a></p>
        <p><strong>2.</strong> Create a new project called "RealEstate"</p>
        <p><strong>3.</strong> Go to <strong>Project Settings -> API</strong></p>
        <p><strong>4.</strong> Copy your <strong>Project URL</strong> and <strong>Anon Key</strong></p>
        <p><strong>5.</strong> Paste them into <code>config.js</code> in this folder.</p>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" class="w-full btn btn-gold py-3 text-sm font-semibold">Got it, let's go!</button>
    </div>
  `;
  document.body.appendChild(modal);
}


let offlineWarningShown = false;
function showOfflineWarning() {
  if (offlineWarningShown) return;
  offlineWarningShown = true;
  window.isOfflineMode = true;
  setTimeout(() => {
    showToast("Database unreachable. Running in Offline Demo Mode.", "warning");
  }, 1000);
}

function isNetworkError(err) {
  if (!err) return false;
  const msg = (err.message || '').toLowerCase();
  const isNet = msg.includes('failed to fetch') || 
                msg.includes('networkerror') || 
                msg.includes('getaddrinfo') ||
                msg.includes('network error') ||
                msg.includes('fetch');
  if (isNet) {
    showOfflineWarning();
  }
  return isNet;
}


// ============================================
// AUTH HELPERS (Supabase based)
// ============================================
const Auth = {
    currentUser: null,

  async checkAndSetGitHub2FA() {
    if (!sb) return;
    try {
      const { data: { session } } = await sb.auth.getSession();
      if (session && session.user) {
        const identities = session.user.identities || [];
        const isGitHub = identities.some(id => id.provider === 'github') || session.user.app_metadata?.provider === 'github';
        if (isGitHub) {
          sessionStorage.setItem('re_2fa_verified_' + session.user.id, 'true');
          localStorage.setItem('re_2fa_verified_' + session.user.id, 'true');
        }
      }
    } catch (e) {
      if (isNetworkError(e)) throw e;
    }
  },

  async isLoggedIn() {
    console.log("[Auth.isLoggedIn] Checking authentication status...");
    // --- Online Supabase session check ---
    if (sb) {
      try {
        const { data: { session } } = await sb.auth.getSession();
        console.log("[Auth.isLoggedIn] Supabase session:", session ? "Active" : "None");
        if (session && session.user) {
          // A valid Supabase session means the user is authenticated.
          // The OTP (2FA) is already enforced during the login flow in login.html.
          console.log("[Auth.isLoggedIn] Valid session found for", session.user.email, "-> true");
          return true;
        }
      } catch (e) {
        console.error("[Auth.isLoggedIn] Online check error:", e);
        isNetworkError(e);
      }
    }
    // --- Offline mock session check ---
    try {
      const session = JSON.parse(localStorage.getItem('sb_offline_session'));
      console.log("[Auth.isLoggedIn] Offline session:", session ? "Active" : "None");
      if (session && session.user) {
        // Offline sessions also require 2FA flag (set during OTP verification)
        const uid = session.user.id;
        const verified = sessionStorage.getItem('re_2fa_verified_' + uid) === 'true' ||
                         localStorage.getItem('re_2fa_verified_' + uid) === 'true';
        console.log(`[Auth.isLoggedIn] Offline user ${uid}, 2FA verified: ${verified}`);
        return verified;
      }
    } catch (e) {
      console.error("[Auth.isLoggedIn] Offline check error:", e);
    }
    console.log("[Auth.isLoggedIn] No active session. Returning false.");
    return false;
  },

  async getUser() {
    console.log("[Auth.getUser] Fetching user profile...");
    if (sb) {
      try {
        const { data: { user } } = await sb.auth.getUser();
        console.log("[Auth.getUser] Supabase user:", user ? user.email : "None");
        if (user) {
          const uid = user.id;
          let { data: profile } = await sb.from('profiles').select('*').eq('id', uid).maybeSingle();
          if (!profile) {
            const metadata = user.user_metadata || {};
            profile = {
              id: uid,
              full_name: metadata.full_name || metadata.name || user.email.split('@')[0],
              role: 'buyer'
            };
            try { await sb.from('profiles').insert(profile); } catch (err) {
              console.warn("Failed to auto-create profile:", err);
            }
          }
          this.currentUser = { id: uid, email: user.email, ...(profile || {}) };
          console.log("[Auth.getUser] Profile loaded:", this.currentUser);
          return this.currentUser;
        }
      } catch (e) {
        console.error("[Auth.getUser] Online user fetch error:", e);
        if (isNetworkError(e)) {
          // Network error - use cached session to avoid unnecessary redirect
          try {
            const { data: { session } } = await sb.auth.getSession();
            if (session && session.user) {
              const uid = session.user.id;
              this.currentUser = {
                id: uid,
                email: session.user.email,
                full_name: session.user.user_metadata?.full_name || session.user.user_metadata?.name || session.user.email.split('@')[0],
                role: 'buyer'
              };
              console.log("[Auth.getUser] Network down. Using cached session:", this.currentUser);
              return this.currentUser;
            }
          } catch (sessionErr) {
            console.error("[Auth.getUser] Failed to load local session:", sessionErr);
          }
        }
      }
    }
    // --- Offline mock session ---
    try {
      const session = JSON.parse(localStorage.getItem('sb_offline_session'));
      if (session && session.user) {
        const uid = session.user.id;
        const verified = sessionStorage.getItem('re_2fa_verified_' + uid) === 'true' ||
                         localStorage.getItem('re_2fa_verified_' + uid) === 'true';
        console.log(`[Auth.getUser] Offline user ${uid}, 2FA verified: ${verified}`);
        if (!verified) { this.currentUser = null; return null; }
        this.currentUser = session.user;
        return this.currentUser;
      }
    } catch (e) {
      console.error("[Auth.getUser] Offline user fetch error:", e);
    }
    console.log("[Auth.getUser] No active user. Returning null.");
    this.currentUser = null;
    return null;
  },

  getUserSync() {
    return this.currentUser;
  },

  async login(email, password) {
    if (!sb) {
      return await this.loginOffline(email, password);
    }
    try {
      const { data, error } = await sb.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return data.user;
    } catch (err) {
      if (isNetworkError(err)) {
        showToast("Database unreachable. Logging in via offline mode.", "warning");
        return await this.loginOffline(email, password);
      }
      try {
        const offlineUser = await this.loginOffline(email, password);
        if (offlineUser) {
          showToast("Using offline local database session.", "info");
          return offlineUser;
        }
      } catch (e) {}
      throw err;
    }
  },

  async loginOffline(email, password) {
    let users = [];
    try { users = JSON.parse(localStorage.getItem('re_users') || '[]'); } catch(e) { users = []; }
    const user = users.find(u => u.email === email);
    if (!user) {
      throw new Error("Invalid email or password");
    }
    const match = (password === user.passwordHash) || (await verifyPassword(password, user.passwordHash));
    if (!match) {
      throw new Error("Invalid email or password");
    }
    localStorage.setItem('sb_offline_session', JSON.stringify({ user }));
    return user;
  },

  async signup(email, password, metadata = {}) {
    if (!sb) {
      return await this.signupOffline(email, password, metadata);
    }
    try {
      const { data, error } = await sb.auth.signUp({
        email,
        password,
        options: { data: metadata }
      });
      if (error) throw error;
      
      if (data.user) {
        await sb.from('profiles').insert({
          id: data.user.id,
          full_name: metadata.fullName || '',
          role: metadata.role || 'buyer'
        });
      }
      return data.user;
    } catch (err) {
      if (isNetworkError(err)) {
        showToast("Database unreachable. Creating offline account.", "warning");
        return await this.signupOffline(email, password, metadata);
      }
      if (err.message && (err.message.toLowerCase().includes('already registered') || err.message.toLowerCase().includes('already exists') || err.status === 422 || err.code === 'user_already_exists')) {
        showToast("Email already registered online. Overwriting locally as offline account.", "info");
        return await this.signupOffline(email, password, metadata);
      }
      throw err;
    }
  },

  async signupOffline(email, password, metadata = {}) {
    let users = [];
    try { users = JSON.parse(localStorage.getItem('re_users') || '[]'); } catch(e) { users = []; }
    
    // Allow re-registration by removing any existing user with the same email
    users = users.filter(u => u.email !== email);
    
    const hashedPassword = await hashPassword(password);
    const user = {
      id: 'off_' + Math.random().toString(36).substr(2, 9),
      email: email,
      full_name: metadata.fullName || '',
      role: metadata.role || 'buyer',
      passwordHash: hashedPassword
    };
    users.push(user);
    localStorage.setItem('re_users', JSON.stringify(users));
    localStorage.setItem('sb_offline_session', JSON.stringify({ user }));
    return user;
  },

  async loginWithGitHub() {
    if (!sb) {
      showToast("Database not connected. GitHub login unavailable in offline mode.", "error");
      throw new Error("Offline mode active");
    }
    try {
      const currentUrl = window.location.href;
      const redirectUrl = currentUrl.substring(0, currentUrl.lastIndexOf('/')) + '/home.html';
      const { error } = await sb.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: redirectUrl
        }
      });
      if (error) throw error;
    } catch (err) {
      if (isNetworkError(err)) {
        showToast("Database unreachable. GitHub login unavailable in offline mode.", "error");
      }
      throw err;
    }
  },

  set2FAVerified(userId, status) {
    console.log(`[Auth.set2FAVerified] Setting 2FA verified for user ${userId} to status ${status}`);
    if (status) {
      sessionStorage.setItem('re_2fa_verified_' + userId, 'true');
      localStorage.setItem('re_2fa_verified_' + userId, 'true');
    } else {
      sessionStorage.removeItem('re_2fa_verified_' + userId);
      localStorage.removeItem('re_2fa_verified_' + userId);
    }
  },

  async logout() {
    if (sb) {
      try {
        const { data: { user } } = await sb.auth.getUser();
        if (user) {
          sessionStorage.removeItem('re_2fa_verified_' + user.id);
          localStorage.removeItem('re_2fa_verified_' + user.id);
        }
      } catch (e) {}
      try { await sb.auth.signOut(); } catch(e) {}
    }
    try {
      const session = JSON.parse(localStorage.getItem('sb_offline_session'));
      if (session && session.user) {
        sessionStorage.removeItem('re_2fa_verified_' + session.user.id);
        localStorage.removeItem('re_2fa_verified_' + session.user.id);
      }
    } catch (e) {}
    localStorage.removeItem('sb_offline_session');
    this.currentUser = null;
    // Only redirect if NOT already on login.html (prevents infinite reload loop)
    const onLoginPage = window.location.href.includes('login.html');
    if (!onLoginPage) {
      window.location.href = 'login.html';
    }
  },

  async signOut() {
    return await this.logout();
  },

  async protect() {
    const logged = await this.isLoggedIn();
    if (!logged) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  },

  async redirectIfLoggedIn() {
    const logged = await this.isLoggedIn();
    if (logged) {
      window.location.href = 'home.html';
    }
  }
};

// Initial state fetch - populate currentUser cache on page load
Auth.getUser().catch(() => {});


// ============================================
// TOAST SYSTEM
// ============================================
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '', error: '', info: '', warning: '' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================
// LOADING SPINNER
// ============================================
function showSpinner() {
  let overlay = document.querySelector('.spinner-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(overlay);
  }
  overlay.classList.add('show');
}

function hideSpinner() {
  const overlay = document.querySelector('.spinner-overlay');
  if (overlay) overlay.classList.remove('show');
}

// ============================================
// PASSWORD HASHING (SHA-256 simulation)
// Real apps use bcrypt on server - ye frontend
// simulation hai jo localStorage ke liye kaafi hai
// ============================================
async function hashPassword(password) {
  const salted = password + 'RE_SALT_2025';
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(salted);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (e) {}
  }
  // JS-only fallback for non-secure contexts (e.g. testing over local network IP)
  let hash = 0;
  for (let i = 0; i < salted.length; i++) {
    const char = salted.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return 'fallback_' + Math.abs(hash).toString(16);
}

async function verifyPassword(plain, hashed) {
  const h = await hashPassword(plain);
  return h === hashed;
}

// ============================================
// OTP GENERATOR
// ============================================
const OTP = {
  generate() {
    return Math.floor(100000 + Math.random() * 900000).toString();
  },

  store(email, otp) {
    const data = { otp, email, expiry: Date.now() + 5 * 60 * 1000 }; // 5 min
    localStorage.setItem('re_otp_' + email, JSON.stringify(data));
  },

  verify(email, enteredOtp) {
    const raw = localStorage.getItem('re_otp_' + email);
    if (!raw) return { valid: false, msg: 'Verification code not found. Please request a new one.' };
    const data = JSON.parse(raw);
    if (Date.now() > data.expiry) {
      localStorage.removeItem('re_otp_' + email);
      return { valid: false, msg: 'Verification code expired. Please request a new one.' };
    }
    if (data.otp !== enteredOtp.trim()) {
      return { valid: false, msg: 'Invalid code. Please try again.' };
    }
    localStorage.removeItem('re_otp_' + email);
    return { valid: true };
  },

  // Simulated send (in real app - email/SMS API)
  send(email, otp) {
    console.log(` OTP for ${email}: ${otp}`); // Dev mode - console mein dikhega
    // Real app mein: EmailJS / Twilio SMS
    return otp;
  }
};

// ============================================
// EMAIL NOTIFICATIONS (EmailJS based)
// ============================================
const EmailNotifications = {
  async sendLoginNotification(email, name) {
    if (typeof emailjs === 'undefined') {
      console.warn("EmailJS library not loaded. Cannot send login notification email.");
      return;
    }
    if (typeof EJ === 'undefined' || EJ.publicKey === 'YOUR_PUBLIC_KEY') {
      showToast(`[Dev Mode] Login confirmation email would be sent to ${email}`, 'info');
      console.info(`[DEV] Login confirmation email sent to ${email}`);
      return;
    }
    try {
      await emailjs.init({ publicKey: EJ.publicKey });
      await emailjs.send(EJ.serviceId, EJ.templateId, {
        to_email: email,
        to_name: name || email.split('@')[0],
        otp_code: 'Success Notification',
        app_name: '🏠 RealEstate',
        message: 'You have successfully signed in to your account. If this was not you, please secure your account immediately.'
      });
      showToast("Sign-in notification email sent!", "success");
    } catch (err) {
      console.error('Failed to send sign-in notification:', err);
    }
  },

  async sendSignupNotification(email, name) {
    if (typeof emailjs === 'undefined') {
      console.warn("EmailJS library not loaded. Cannot send welcome email.");
      return;
    }
    if (typeof EJ === 'undefined' || EJ.publicKey === 'YOUR_PUBLIC_KEY') {
      showToast(`[Dev Mode] Welcome email would be sent to ${email}`, 'info');
      console.info(`[DEV] Welcome email sent to ${email}`);
      return;
    }
    try {
      await emailjs.init({ publicKey: EJ.publicKey });
      await emailjs.send(EJ.serviceId, EJ.templateId, {
        to_email: email,
        to_name: name || email.split('@')[0],
        otp_code: 'Success Registration',
        app_name: '🏠 RealEstate',
        message: 'Welcome to RealEstate! Your account has been successfully created and verified.'
      });
      showToast("Welcome email sent!", "success");
    } catch (err) {
      console.error('Failed to send welcome email:', err);
    }
  }
};

// ============================================
// ACCOUNT LOCK SYSTEM
// 5 galat attempts -> 15 min lock
// ============================================
const AccountLock = {
  MAX_ATTEMPTS: 5,
  LOCK_DURATION: 15 * 60 * 1000, // 15 minutes

  getAttempts(email) {
    const raw = localStorage.getItem('re_attempts_' + email);
    return raw ? JSON.parse(raw) : { count: 0, lockedUntil: null };
  },

  recordFail(email) {
    const data = this.getAttempts(email);
    data.count++;
    if (data.count >= this.MAX_ATTEMPTS) {
      data.lockedUntil = Date.now() + this.LOCK_DURATION;
      data.count = 0;
    }
    localStorage.setItem('re_attempts_' + email, JSON.stringify(data));
    return data;
  },

  reset(email) {
    localStorage.removeItem('re_attempts_' + email);
  },

  isLocked(email) {
    const data = this.getAttempts(email);
    if (!data.lockedUntil) return { locked: false };
    if (Date.now() < data.lockedUntil) {
      const mins = Math.ceil((data.lockedUntil - Date.now()) / 60000);
      return { locked: true, mins };
    }
    this.reset(email); // Lock expired
    return { locked: false };
  },

  getRemainingAttempts(email) {
    const data = this.getAttempts(email);
    return Math.max(0, this.MAX_ATTEMPTS - data.count);
  }
};

// ============================================
// RBAC - ROLE-BASED ACCESS CONTROL
// Roles: buyer | seller | agent | admin
// ============================================
const RBAC = {
  ROLES: {
    buyer:  { canBuy: true,  canSell: false, canList: false, canManage: false },
    seller: { canBuy: false, canSell: true,  canList: true,  canManage: false },
    agent:  { canBuy: true,  canSell: true,  canList: true,  canManage: false },
    admin:  { canBuy: true,  canSell: true,  canList: true,  canManage: true  }
  },

  getUserRole() {
    const user = Auth.getUserSync();
    return user?.role || 'buyer';
  },

  can(permission) {
    const role = this.getUserRole();
    return this.ROLES[role]?.[permission] || false;
  },

  getRoleLabel(role) {
    const labels = { buyer: ' Buyer', seller: ' Seller', agent: ' Agent', admin: ' Admin' };
    return labels[role] || ' Buyer';
  }
};


// ============================================
// DATA STORE (localStorage based)
// ============================================
// ============================================
// DATA STORE (Supabase based)
// ============================================
const Store = {
  set(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  },

  // Helper to map DB fields to UI fields
  _map(p) {
    if (!p) return null;
    return {
      ...p,
      listingType: p.listing_type || p.listingType,
      dealScore: p.deal_score || p.dealScore,
      contactName: p.contact_name || p.contactName,
      contactPhone: p.contact_phone || p.contactPhone,
      isVerified: p.is_verified || p.isVerified,
      totalViews: p.total_views || p.totalViews
    };
  },

  _mapReverse(p) {
    if (!p) return null;
    const out = { ...p };
    if (p.listingType) { out.listing_type = p.listingType; delete out.listingType; }
    if (p.dealScore) { out.deal_score = p.dealScore; delete out.dealScore; }
    if (p.contactName) { out.contact_name = p.contactName; delete out.contactName; }
    if (p.contactPhone) { out.contact_phone = p.contactPhone; delete out.contactPhone; }
    if (p.isVerified) { out.is_verified = p.isVerified; delete out.isVerified; }
    if (p.totalViews) { out.total_views = p.totalViews; delete out.totalViews; }
    return out;
  },

  // --- PROPERTIES ---
  async getProperties() {
    if (!sb) return this.getPropertiesOffline();
    try {
      const { data, error } = await sb.from('properties').select('*').order('created_at', { ascending: false });
      if (error) throw error;
      return data.map(p => this._map(p));
    } catch(e) {
      if (isNetworkError(e)) {
        return this.getPropertiesOffline();
      }
      console.error('getProperties error:', e);
      return [];
    }
  },

  getPropertiesOffline() {
    try {
      return JSON.parse(localStorage.getItem('re_properties') || '[]').map(p => this._map(p));
    } catch(e) { return []; }
  },

  async addProperty(prop) {
    if (!sb) return this.addPropertyOffline(prop);
    const user = await Auth.getUser();
    if (!user) return false;
    const mapped = this._mapReverse(prop);
    try {
      const { error } = await sb.from('properties').insert({ ...mapped, owner_id: user.id });
      if (error) throw error;
      return true;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.addPropertyOffline(prop);
      }
      showToast(e.message, 'error');
      return false;
    }
  },

  addPropertyOffline(prop) {
    const user = Auth.getUserSync();
    if (!user) return false;
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    const newProp = {
      ...prop,
      id: 'prop_' + Math.random().toString(36).substr(2, 9),
      ownerId: user.id,
      createdAt: new Date().toISOString()
    };
    props.unshift(newProp);
    localStorage.setItem('re_properties', JSON.stringify(props));
    return true;
  },

  async getPropertyById(id) {
    if (!sb) return this.getPropertyByIdOffline(id);
    try {
      const { data, error } = await sb.from('properties').select('*').eq('id', id).single();
      if (error) throw error;
      return this._map(data);
    } catch(e) {
      if (isNetworkError(e)) {
        return this.getPropertyByIdOffline(id);
      }
      return null;
    }
  },

  getPropertyByIdOffline(id) {
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    const found = props.find(p => p.id === id);
    return found ? this._map(found) : null;
  },

  async updateProperty(id, updates) {
    if (!sb) return this.updatePropertyOffline(id, updates);
    const mapped = this._mapReverse(updates);
    try {
      const { error } = await sb.from('properties').update(mapped).eq('id', id);
      if (error) throw error;
      return true;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.updatePropertyOffline(id, updates);
      }
      showToast(e.message, 'error');
      return false;
    }
  },

  updatePropertyOffline(id, updates) {
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    const idx = props.findIndex(p => p.id === id);
    if (idx === -1) return false;
    props[idx] = { ...props[idx], ...updates };
    localStorage.setItem('re_properties', JSON.stringify(props));
    return true;
  },

  async deleteProperty(id) {
    if (!sb) return this.deletePropertyOffline(id);
    try {
      const { error } = await sb.from('properties').delete().eq('id', id);
      if (error) throw error;
      return true;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.deletePropertyOffline(id);
      }
      showToast(e.message, 'error');
      return false;
    }
  },

  deletePropertyOffline(id) {
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    props = props.filter(p => p.id !== id);
    localStorage.setItem('re_properties', JSON.stringify(props));
    return true;
  },

  async getUserProperties() {
    if (!sb) return this.getUserPropertiesOffline();
    const user = await Auth.getUser();
    if (!user) return [];
    try {
      const { data, error } = await sb.from('properties').select('*').eq('owner_id', user.id);
      if (error) throw error;
      return data.map(p => this._map(p));
    } catch(e) {
      if (isNetworkError(e)) {
        return this.getUserPropertiesOffline();
      }
      return [];
    }
  },

  getUserPropertiesOffline() {
    const user = Auth.getUserSync();
    if (!user) return [];
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    return props.filter(p => p.ownerId === user.id || p.owner_id === user.id).map(p => this._map(p));
  },

  // --- FAVORITES ---
  async getFavorites() {
    if (!sb) return this.getFavoritesOffline();
    const user = await Auth.getUser();
    if (!user) return [];
    try {
      const { data, error } = await sb.from('favorites').select('property_id, properties(*)').eq('user_id', user.id);
      if (error) throw error;
      return data.map(f => this._map(f.properties)).filter(Boolean);
    } catch(e) {
      if (isNetworkError(e)) {
        return this.getFavoritesOffline();
      }
      return [];
    }
  },

  getFavoritesOffline() {
    const user = Auth.getUserSync();
    if (!user) return [];
    let favIds = [];
    try { favIds = JSON.parse(localStorage.getItem('re_favs_' + user.id) || '[]'); } catch(e) {}
    let props = [];
    try { props = JSON.parse(localStorage.getItem('re_properties') || '[]'); } catch(e) {}
    return props.filter(p => favIds.includes(p.id)).map(p => this._map(p));
  },

  async isFavorite(propId) {
    if (!sb) return this.isFavoriteOffline(propId);
    const user = await Auth.getUser();
    if (!user) return false;
    try {
      const { data } = await sb.from('favorites').select('id').match({ user_id: user.id, property_id: propId }).maybeSingle();
      return !!data;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.isFavoriteOffline(propId);
      }
      return false;
    }
  },

  isFavoriteOffline(propId) {
    const user = Auth.getUserSync();
    if (!user) return false;
    let favIds = [];
    try { favIds = JSON.parse(localStorage.getItem('re_favs_' + user.id) || '[]'); } catch(e) {}
    return favIds.includes(propId);
  },

  async toggleFavorite(prop) {
    if (!sb) return this.toggleFavoriteOffline(prop);
    const user = await Auth.getUser();
    if (!user) { showToast('Please sign in first', 'warning'); return false; }
    try {
      const isFav = await this.isFavorite(prop.id);
      if (isFav) {
        await sb.from('favorites').delete().match({ user_id: user.id, property_id: prop.id });
        return false;
      } else {
        await sb.from('favorites').insert({ user_id: user.id, property_id: prop.id });
        return true;
      }
    } catch(e) {
      if (isNetworkError(e)) {
        return this.toggleFavoriteOffline(prop);
      }
      return false;
    }
  },

  toggleFavoriteOffline(prop) {
    const user = Auth.getUserSync();
    if (!user) return false;
    let favIds = [];
    try { favIds = JSON.parse(localStorage.getItem('re_favs_' + user.id) || '[]'); } catch(e) {}
    const idx = favIds.indexOf(prop.id);
    let added = false;
    if (idx > -1) {
      favIds.splice(idx, 1);
    } else {
      favIds.push(prop.id);
      added = true;
    }
    localStorage.setItem('re_favs_' + user.id, JSON.stringify(favIds));
    return added;
  },

  // --- MESSAGES ---
  async getMessages() {
    if (!sb) return this.getMessagesOffline();
    const user = await Auth.getUser();
    if (!user) return [];
    try {
      const { data, error } = await sb.from('messages').select('*')
        .or(`sender_id.eq.${user.id},receiver_id.eq.${user.id}`)
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.getMessagesOffline();
      }
      return [];
    }
  },

  getMessagesOffline() {
    const user = Auth.getUserSync();
    if (!user) return [];
    let msgs = [];
    try { msgs = JSON.parse(localStorage.getItem('re_messages') || '[]'); } catch(e) {}
    return msgs.filter(m => m.sender_id === user.id || m.receiver_id === user.id);
  },

  async sendMessage(receiver_id, text, property_id) {
    if (!sb) return this.sendMessageOffline(receiver_id, text, property_id);
    const user = await Auth.getUser();
    if (!user) return false;
    try {
      const { error } = await sb.from('messages').insert({
        sender_id: user.id, receiver_id, text, property_id
      });
      if (error) throw error;
      return true;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.sendMessageOffline(receiver_id, text, property_id);
      }
      showToast(e.message, 'error');
      return false;
    }
  },

  sendMessageOffline(receiver_id, text, property_id) {
    const user = Auth.getUserSync();
    if (!user) return false;
    let msgs = [];
    try { msgs = JSON.parse(localStorage.getItem('re_messages') || '[]'); } catch(e) {}
    msgs.push({
      id: 'msg_' + Math.random().toString(36).substr(2, 9),
      sender_id: user.id,
      receiver_id,
      text,
      property_id,
      created_at: new Date().toISOString()
    });
    localStorage.setItem('re_messages', JSON.stringify(msgs));
    return true;
  },

  // --- USER PROFILE ---
  async updateProfile(data) {
    if (!sb) return this.updateProfileOffline(data);
    const user = await Auth.getUser();
    if (!user) return null;
    try {
      const { error } = await sb.from('profiles').update(data).eq('id', user.id);
      if (error) throw error;
      return { ...user, ...data };
    } catch(e) {
      if (isNetworkError(e)) {
        return this.updateProfileOffline(data);
      }
      showToast(e.message, 'error');
      return null;
    }
  },

  updateProfileOffline(data) {
    const user = Auth.getUserSync();
    if (!user) return null;
    let users = [];
    try { users = JSON.parse(localStorage.getItem('re_users') || '[]'); } catch(e) {}
    const idx = users.findIndex(u => u.id === user.id);
    if (idx > -1) {
      users[idx] = { ...users[idx], ...data };
      localStorage.setItem('re_users', JSON.stringify(users));
    }
    try {
      const session = JSON.parse(localStorage.getItem('sb_offline_session'));
      if (session && session.user && session.user.id === user.id) {
        session.user = { ...session.user, ...data };
        localStorage.setItem('sb_offline_session', JSON.stringify(session));
      }
    } catch(e) {}
    return { ...user, ...data };
  },

  async search(params = {}) {
    if (!sb) return this.searchOffline(params);
    const {
      q           = '',
      listingType = 'all',
      minPrice    = 0,
      maxPrice    = Infinity,
      maxUnbounded = true,
      types       = [],
      bhk         = [],
      deals       = [],
      sort        = 'newest'
    } = params;

    try {
      let query = sb.from('properties').select('*');
      if (listingType !== 'all') query = query.eq('listing_type', listingType);
      if (minPrice > 0) query = query.gte('price', minPrice);
      if (!maxUnbounded) query = query.lte('price', maxPrice);
      if (types && types.length) query = query.in('category', types);
      if (bhk && bhk.length) query = query.in('bedrooms', bhk);
      if (deals && deals.length) query = query.in('deal_score', deals);
      if (sort === 'price-lo') query = query.order('price', { ascending: true });
      else if (sort === 'price-hi') query = query.order('price', { ascending: false });
      else if (sort === 'area') query = query.order('area', { ascending: false });
      else query = query.order('created_at', { ascending: false });

      const { data, error } = await query;
      if (error) throw error;

      let results = data.map(p => this._map(p));
      if (q) {
        const lq = q.toLowerCase();
        results = results.filter(p =>
          (p.title + ' ' + (p.location || p.city || '')).toLowerCase().includes(lq)
        );
      }
      return results;
    } catch(e) {
      if (isNetworkError(e)) {
        return this.searchOffline(params);
      }
      console.error('search error:', e);
      return [];
    }
  },

  searchOffline(params = {}) {
    const {
      q           = '',
      listingType = 'all',
      minPrice    = 0,
      maxPrice    = Infinity,
      maxUnbounded = true,
      types       = [],
      bhk         = [],
      deals       = [],
      sort        = 'newest'
    } = params;

    let results = this.getPropertiesOffline();

    if (listingType !== 'all') {
      results = results.filter(p => p.listingType === listingType);
    }
    results = results.filter(p => p.price >= minPrice);
    if (!maxUnbounded) {
      results = results.filter(p => p.price <= maxPrice);
    }
    if (types && types.length) {
      results = results.filter(p => types.includes(p.category));
    }
    if (bhk && bhk.length) {
      results = results.filter(p => bhk.includes(p.bedrooms));
    }
    if (deals && deals.length) {
      results = results.filter(p => deals.includes(p.dealScore));
    }

    if (q) {
      const lq = q.toLowerCase();
      results = results.filter(p =>
        (p.title + ' ' + (p.location || p.city || '')).toLowerCase().includes(lq)
      );
    }

    if (sort === 'price-lo') {
      results.sort((a, b) => a.price - b.price);
    } else if (sort === 'price-hi') {
      results.sort((a, b) => b.price - a.price);
    } else if (sort === 'area') {
      results.sort((a, b) => b.area - a.area);
    } else {
      results.sort((a, b) => new Date(b.createdAt || b.created_at) - new Date(a.createdAt || a.created_at));
    }
    return results;
  }
};


function getDefaultMessages() {
  return [
    {
      id: 'conv1',
      name: 'Rahul Sharma',
      avatar: 'R',
      property: 'Sea View Apartment',
      preview: 'Is the price negotiable?',
      time: '10:30 AM',
      unread: true,
      messages: [
        { text: 'Hello! I had a question about the Sea View Apartment.', time: '10:25 AM', sent: false },
        { text: 'Sure, what would you like to know?', time: '10:27 AM', sent: true },
        { text: 'Is the price negotiable?', time: '10:30 AM', sent: false }
      ]
    },
    {
      id: 'conv2',
      name: 'Priya Singh',
      avatar: 'P',
      property: 'Modern Villa',
      preview: 'Would like to schedule a visit tomorrow',
      time: 'Yesterday',
      unread: false,
      messages: [
        { text: 'Saw the photos of the Modern Villa. Looks amazing!', time: 'Yesterday 2:00 PM', sent: false },
        { text: 'Thank you! Would you like to schedule a visit?', time: 'Yesterday 2:15 PM', sent: true },
        { text: 'Would like to schedule a visit tomorrow', time: 'Yesterday 3:00 PM', sent: false }
      ]
    },
    {
      id: 'conv3',
      name: 'Amit Patel',
      avatar: 'A',
      property: 'Studio Apartment',
      preview: 'When is it available for rent?',
      time: 'Mon',
      unread: false,
      messages: [
        { text: 'I wanted to ask about the Studio Apartment.', time: 'Mon 9:00 AM', sent: false },
        { text: 'When is it available for rent?', time: 'Mon 9:05 AM', sent: false },
        { text: 'It is available from the 1st!', time: 'Mon 10:00 AM', sent: true }
      ]
    }
  ];
}

// ============================================
// HAMBURGER + SIDEBAR
// ============================================
function initSidebar() {
  // ── Guard: prevent double-binding if called more than once ──────────────
  if (window._sidebarInitDone) return;
  window._sidebarInitDone = true;

  const sidebar   = document.getElementById('sidebar');
  const hamburger = document.getElementById('hamburger');
  const overlay   = document.getElementById('overlay');

  // ── Inject Property Catalog link if missing ─────────────────────────────
  if (sidebar && !sidebar.querySelector('a[href="property-catalog.html"]')) {
    const myPropsLink = sidebar.querySelector('a[href="properties.html"]');
    const catalogLink = document.createElement('a');
    catalogLink.href = 'property-catalog.html';
    catalogLink.innerHTML = '<span class="nav-icon">📋</span> Property Catalog<span class="nav-arrow">›</span>';
    if (myPropsLink) myPropsLink.after(catalogLink);
    else if (sidebar) sidebar.appendChild(catalogLink);
  }

  // ── No sidebar or hamburger on this page (home/login/signup) → exit ─────
  if (!hamburger || !sidebar) return;

  // ── Open / Close helpers ────────────────────────────────────────────────
  function openSidebar() {
    hamburger.classList.add('open');
    sidebar.classList.add('active');
    if (overlay) { overlay.classList.add('active'); }
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    hamburger.classList.remove('open');
    sidebar.classList.remove('active');
    if (overlay) { overlay.classList.remove('active'); }
    document.body.style.overflow = '';
  }

  // ── Hamburger toggle ────────────────────────────────────────────────────
  hamburger.addEventListener('click', () => {
    sidebar.classList.contains('active') ? closeSidebar() : openSidebar();
  });

  // ── Overlay click closes sidebar ────────────────────────────────────────
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // ── Escape key closes sidebar ───────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // ── Nav link click closes sidebar on mobile ─────────────────────────────
  sidebar.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      // Only close — don't prevent navigation
      closeSidebar();
    });
  });

  // ── Highlight the active page link ──────────────────────────────────────
  // pathname.split('/').pop() gives '' for root '/' → fall back to 'index.html'
  // Also handles query strings like 'index.html?foo=bar'
  const rawPage    = window.location.pathname.split('/').pop();
  const currentPage = (rawPage && rawPage !== '') ? rawPage.split('?')[0] : 'index.html';

  sidebar.querySelectorAll('a[href]').forEach(link => {
    const href = (link.getAttribute('href') || '').split('?')[0];
    if (href === currentPage) {
      link.classList.add('active-link');
    } else {
      link.classList.remove('active-link'); // clean up any stale highlight
    }
  });
}

// ============================================
// WELCOME MESSAGE
// ============================================
async function initWelcome() {
  const welcomeEl = document.getElementById('welcomeMsg');
  if (!welcomeEl) return;

  // Use cached user first for instant display, then fetch fresh
  const user = Auth.currentUser || await Auth.getUser();
  if (user) {
    welcomeEl.textContent = `Welcome, ${user.full_name || user.fullName || user.email.split('@')[0]} `;
  }
}

// ============================================
// LOGOUT BUTTON
// ============================================
async function initLogout() {
  const btn = document.getElementById('logoutBtn');
  if (!btn) return;

  const user = Auth.currentUser || await Auth.getUser();
  if (user) {
    btn.style.display = 'flex';
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (confirm('Are you sure you want to sign out?')) {
        Auth.logout();
      }
    });
  }
}

// ============================================
// PROPERTY CARD RENDERER
// ============================================
// ============================================
// CANONICAL PROPERTY CARD RENDERER
// Supports all contexts: home, favorites, profile, dashboard
// options: { index, showEdit, showDelete, showFav }
// ============================================
function renderPropertyCard(prop, options = {}) {
  const { showEdit = false, showDelete = false, showFav = true, isFavorite = false } = options;

  const card = document.createElement('div');
  card.className = 'prop-card';
  card.style.animationDelay = `${(options.index || 0) * 0.06}s`;

  const badge = prop.listingType === 'Rent' ? 'rent' : 'sale';

  let dealHtml = '';
  if (prop.dealScore) {
    const dealColors = {
      'Great Deal': { bg: '#22c55e', color: '#fff' },
      'Fair Price':  { bg: '#e6b94a', color: '#000' },
      'Overpriced':  { bg: '#ef4444', color: '#fff' }
    };
    const dc = dealColors[prop.dealScore] || { bg: '#888', color: '#fff' };
    dealHtml = `<span style="position:absolute;top:10px;right:10px;background:${dc.bg};color:${dc.color};padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;text-transform:uppercase;">${prop.dealScore}</span>`;
  }

  const bedsHtml = (+prop.bedrooms > 0) ? `<span>\uD83D\uDECF ${prop.bedrooms} BHK</span>` : '';
  const bathHtml = prop.bathrooms ? `<span>\uD83D\uDEB0 ${prop.bathrooms} Bath</span>` : '';

  card.innerHTML = `
    <div class="prop-card-img" style="position:relative;">
      <img src="${prop.image || 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600'}"
           alt="${prop.title}"
           style="width:100%;height:190px;object-fit:cover;display:block;"
           onerror="this.src='https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600'">
      <span class="prop-badge ${badge}">${prop.listingType || 'Sale'}</span>
      ${dealHtml}
    </div>
    <div class="prop-card-body">
      <h3 style="margin:0 0 4px;font-size:0.95rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${prop.title}</h3>
      <p class="prop-location">\uD83D\uDCCD ${prop.location}</p>
      <div class="prop-meta">${bedsHtml}<span>\uD83D\uDCCF ${prop.area} sqft</span>${bathHtml}</div>
      <div class="prop-price">${formatCurrency(prop.price)}</div>
      <div class="prop-actions">
        ${showEdit
          ? `<button class="btn btn-outline btn-sm" onclick="window.location.href='add-property.html?edit=${prop.id}'">\u270F\uFE0F Edit</button>`
          : `<a href="property-detail.html?id=${prop.id}" class="btn btn-gold btn-sm">View Details</a>`}
        ${showDelete ? `<button class="btn btn-danger btn-sm" onclick="deletePropertyById('${prop.id}', this)">\uD83D\uDDD1\uFE0F Delete</button>` : ''}
        ${showFav ? `<button class="btn btn-outline btn-sm fav-btn" data-id="${prop.id}" onclick="handleFav('${prop.id}', this)">${isFavorite ? '\u2764\uFE0F' : '\uD83E\uDD0D'}</button>` : ''}
      </div>
    </div>
  `;

  return card;
}

// ============================================
// EMPTY STATE HELPER
// Renders a "no properties found" message into a container.
// ============================================
function renderEmptyState(container, message = 'No properties found', hint = 'Try adjusting your filters') {
  container.innerHTML =
    '<div class="empty-state">' +
      '<span class="empty-icon">\uD83D\uDD0D</span>' +
      '<h3>' + message + '</h3>' +
      '<p>' + hint + '</p>' +
      '<button class="btn btn-gold" onclick="clearAll && clearAll()">Clear Filters</button>' +
    '</div>';
}

// ============================================
// SKELETON LOADER GRID
// Shows 6 shimmering skeleton cards
// ============================================
function renderSkeletonGrid(containerId, count = 6) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const card = document.createElement('div');
    card.className = 'prop-card is-skeleton skeleton';
    card.style.animationDelay = (i * 0.1) + 's';
    card.innerHTML = `
      <div class="prop-card-img" style="background:transparent;"></div>
      <div class="prop-card-body">
        <div class="skeleton skeleton-text medium"></div>
        <div class="skeleton skeleton-text short" style="margin-bottom:14px;"></div>
        <div style="display:flex;gap:6px;margin-bottom:12px;">
          <div class="skeleton" style="width:50px;height:24px;border-radius:4px;"></div>
          <div class="skeleton" style="width:60px;height:24px;border-radius:4px;"></div>
        </div>
        <div class="skeleton skeleton-text short" style="margin-top:auto;padding-top:10px;"></div>
      </div>
    `;
    container.appendChild(card);
  }
}

// ============================================
// PROPERTY GRID RENDERER
// High-level helper: clears container, fills with cards (or empty state).
// options passed through to renderPropertyCard
// ============================================
function renderPropertyGrid(container, props, options = {}) {
  if (typeof container === 'string') container = document.getElementById(container);
  if (!container) return;

  container.innerHTML = '';

  if (!props || props.length === 0) {
    renderEmptyState(container, options.emptyMessage, options.emptyHint);
    return;
  }

  props.forEach((p, i) => {
    container.appendChild(renderPropertyCard(p, { ...options, index: i }));
  });
}

// ============================================
// CANONICAL CURRENCY FORMATTER
// Returns a Rs. -prefixed string (e.g. Rs. 12.50 Cr)
// ============================================
function formatCurrency(price) {
  const n = parseFloat(price);
  if (isNaN(n)) return 'Rs. 0';
  if (n >= 10000000) return '\u20B9' + (n / 10000000).toFixed(2) + ' Cr';
  if (n >= 100000)   return '\u20B9' + (n / 100000).toFixed(2) + ' L';
  return '\u20B9' + n.toLocaleString('en-IN');
}

// Legacy alias - keeps older call sites working
function formatPrice(price) { return formatCurrency(price).replace('\u20B9', ''); }

function viewProperty(id) {
  window.location.href = `property-detail.html?id=${id}`;
}

async function handleFav(propId, btn) {
  // Auth check must be awaited - isLoggedIn() is async
  const logged = await Auth.isLoggedIn();
  if (!logged) {
    showToast('Please sign in to save favorites', 'warning');
    return;
  }
  const props = await Store.getProperties();
  const prop = props.find(p => p.id === propId);
  if (!prop) return;

  const added = await Store.toggleFavorite(prop);
  btn.textContent = added ? '❤️' : '🤍';
  showToast(added ? 'Added to favorites! ❤️' : 'Removed from favorites', added ? 'success' : 'info');
}

function deletePropertyById(id, btn) {
  if (!confirm('Are you sure you want to delete this property?')) return;
  Store.deleteProperty(id);
  const card = btn.closest('.prop-card');
  if (card) {
    card.style.opacity = '0';
    card.style.transform = 'scale(0.9)';
    card.style.transition = 'all 0.3s ease';
    setTimeout(() => card.remove(), 300);
  }
  showToast('Property deleted successfully!', 'success');
}

// ============================================
// INPUT SANITIZER
// ============================================
function sanitize(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(str || '')));
  return d.innerHTML;
}

// ============================================
// FORM VALIDATORS
// ============================================
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

function validatePhone(phone) {
  return /^[6-9]\d{9}$/.test(phone.replace(/\s/g, ''));
}

function validatePassword(pass) {
  if (pass.length < 6) return 'Password must be at least 6 characters';
  if (!/[A-Z]/.test(pass)) return 'Must include at least one uppercase letter';
  if (!/[0-9]/.test(pass)) return 'Must include at least one number';
  return null;
}

function showError(inputEl, msg) {
  if (!inputEl) return;
  inputEl.style.borderColor = 'var(--error)';
  let errEl = inputEl.parentElement.querySelector('.form-error');
  if (!errEl) {
    errEl = document.createElement('p');
    errEl.className = 'form-error';
    inputEl.parentElement.appendChild(errEl);
  }
  errEl.textContent = msg;
  errEl.classList.add('show');
}

function clearError(inputEl) {
  if (!inputEl) return;
  inputEl.style.borderColor = '';
  const errEl = inputEl.parentElement.querySelector('.form-error');
  if (errEl) errEl.classList.remove('show');
}

// ============================================
// INIT ON EVERY PAGE
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initWelcome();
  initLogout();
  initPageSpecific();
});

// Page-specific init (overridden per page)
function initPageSpecific() {}

// ============================================
// SEED DEMO PROPERTIES (shown on fresh load)
// ============================================
async function seedDemoProperties() {
  let existing = await Store.getProperties();
  // Filter out old corrupted demo data (missing ownerId or using old 'd1' format)
  const validProps = existing.filter(p => (p.ownerId || p.owner_id) && (p.ownerId || p.owner_id) !== 'demo' && !p.id.startsWith('d'));
  
  // If we already have the correct 12 demo properties, don't re-seed
  const hasDemo = existing.filter(p => (p.ownerId || p.owner_id) === 'demo').length >= 12;
  if (hasDemo) {
    // Just ensure localStorage is clean of old corruption
    if (existing.length !== validProps.length + 12) {
      Store.set('re_properties', validProps.concat(existing.filter(p => (p.ownerId || p.owner_id) === 'demo')));
    }
    return;
  }

  const demos = [
    {
      id: 'demo1', title: '3 BHK Sea View Apartment', listingType: 'Sale',
      category: 'Apartment', city: 'Mumbai', locality: 'Bandra West',
      location: 'Bandra West, Mumbai', price: 12500000, bedrooms: 3,
      bathrooms: 2, area: 1450, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=600',
      amenities: ['Parking','Gym','Lift','Security'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo2', title: 'Luxurious 4 BHK Villa', listingType: 'Sale',
      category: 'Villa', city: 'Bangalore', locality: 'Whitefield',
      location: 'Whitefield, Bangalore', price: 18000000, bedrooms: 4,
      bathrooms: 4, area: 3200, dealScore: 'Great Deal',
      image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600',
      amenities: ['Parking','Pool','Garden','Security','Power Backup'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo3', title: 'Cozy 2 BHK Apartment', listingType: 'Rent',
      category: 'Apartment', city: 'Pune', locality: 'Koregaon Park',
      location: 'Koregaon Park, Pune', price: 35000, bedrooms: 2,
      bathrooms: 2, area: 1100, dealScore: 'Great Deal',
      image: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600',
      amenities: ['Parking','Gym','Lift','Furnished'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo4', title: 'Modern Studio Apartment', listingType: 'Rent',
      category: 'Apartment', city: 'Delhi', locality: 'Connaught Place',
      location: 'Connaught Place, Delhi', price: 28000, bedrooms: 1,
      bathrooms: 1, area: 620, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600',
      amenities: ['Lift','Security','Furnished'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo5', title: 'Spacious 3 BHK Independent House', listingType: 'Sale',
      category: 'House', city: 'Hyderabad', locality: 'Jubilee Hills',
      location: 'Jubilee Hills, Hyderabad', price: 9500000, bedrooms: 3,
      bathrooms: 3, area: 2200, dealScore: 'Great Deal',
      image: 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600',
      amenities: ['Parking','Garden','Security'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo6', title: 'Premium 2 BHK Near Metro', listingType: 'Rent',
      category: 'Apartment', city: 'Noida', locality: 'Sector 62',
      location: 'Sector 62, Noida', price: 22000, bedrooms: 2,
      bathrooms: 2, area: 980, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=600',
      amenities: ['Parking','Lift','Power Backup'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo7', title: 'Elegant 5 BHK Bungalow', listingType: 'Sale',
      category: 'Villa', city: 'Chennai', locality: 'Adyar',
      location: 'Adyar, Chennai', price: 25000000, bedrooms: 5,
      bathrooms: 5, area: 4500, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=600',
      amenities: ['Parking','Pool','Gym','Garden','Security','Power Backup'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo8', title: '1 BHK Affordable Flat', listingType: 'Sale',
      category: 'Apartment', city: 'Ahmedabad', locality: 'Satellite',
      location: 'Satellite, Ahmedabad', price: 3200000, bedrooms: 1,
      bathrooms: 1, area: 680, dealScore: 'Great Deal',
      image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600',
      amenities: ['Lift','Parking'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo9', title: 'Fully Furnished 3 BHK', listingType: 'Rent',
      category: 'Apartment', city: 'Gurgaon', locality: 'DLF Phase 2',
      location: 'DLF Phase 2, Gurgaon', price: 55000, bedrooms: 3,
      bathrooms: 3, area: 1800, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=600',
      amenities: ['Parking','Gym','Pool','Lift','Furnished','Security'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo10', title: 'Commercial Office Space', listingType: 'Rent',
      category: 'Commercial', city: 'Bangalore', locality: 'MG Road',
      location: 'MG Road, Bangalore', price: 120000, bedrooms: 0,
      bathrooms: 2, area: 2400, dealScore: 'Fair Price',
      image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600',
      amenities: ['Parking','Lift','Power Backup','Security'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo11', title: 'Budget 2 BHK Society Flat', listingType: 'Sale',
      category: 'Apartment', city: 'Kolkata', locality: 'Salt Lake',
      location: 'Salt Lake, Kolkata', price: 4800000, bedrooms: 2,
      bathrooms: 2, area: 1050, dealScore: 'Great Deal',
      image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600',
      amenities: ['Lift','Parking','Security'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    },
    {
      id: 'demo12', title: 'Penthouse with Terrace', listingType: 'Sale',
      category: 'Apartment', city: 'Mumbai', locality: 'Worli',
      location: 'Worli, Mumbai', price: 45000000, bedrooms: 4,
      bathrooms: 4, area: 5200, dealScore: 'Overpriced',
      image: 'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600',
      amenities: ['Parking','Pool','Gym','Lift','Furnished','Security','Garden'],
      ownerId: 'demo', createdAt: new Date().toISOString()
    }
  ];

  Store.set('re_properties', [...validProps, ...demos]);
}

// Auto-seed on first load
seedDemoProperties().catch(err => console.error("Seeding error:", err));

// ============================================
// AI-BASED PRICE PREDICTION
// Simple ML-style rule engine (no API needed)
// ============================================
const AIPricePrediction = {
  cityRates: {
    'mumbai': 22000, 'pune': 7500, 'bangalore': 9000, 'bengaluru': 9000,
    'delhi': 11000, 'new delhi': 11000, 'gurgaon': 12000, 'gurugram': 12000,
    'noida': 7000, 'hyderabad': 7500, 'chennai': 7000, 'kolkata': 5500,
    'ahmedabad': 5000, 'surat': 4500, 'jaipur': 5000, 'lucknow': 4000,
    'bhopal': 4000, 'nagpur': 4500, 'indore': 5000, 'chandigarh': 6000,
    'kochi': 6500, 'coimbatore': 4500, 'thane': 13000, 'navi mumbai': 11000, 'palghar': 4000
  },
  bhkMultiplier: { 1: 0.85, 2: 1.0, 3: 1.1, 4: 1.2, 5: 1.3 },

  predict({ city, area, bedrooms }) {
    const baseRate = this.cityRates[(city||'').toLowerCase().trim()] || 6000;
    const sqft = parseFloat(area) || 1000;
    const mul  = this.bhkMultiplier[parseInt(bedrooms)] || 1.0;
    const predicted = Math.round(baseRate * sqft * mul);
    const low  = Math.round(predicted * 0.85);
    const high = Math.round(predicted * 1.15);
    const fmt  = n => n >= 10000000 ? (n/10000000).toFixed(2)+' Cr' : (n/100000).toFixed(1)+' L';
    return {
      predicted, low, high,
      perSqft: baseRate,
      confidence: this.cityRates[(city||'').toLowerCase()] ? 'High' : 'Medium',
      label: 'Rs. ' + fmt(predicted),
      range: 'Rs. ' + fmt(low) + '  Rs. ' + fmt(high)
    };
  },

  getDealScore(actualPrice, predictedPrice) {
    const ratio = actualPrice / predictedPrice;
    if (ratio < 0.85) return { score: 'Great Deal', color: '#22c55e', icon: '', diff: Math.round((1-ratio)*100) + '% below market' };
    if (ratio < 1.05) return { score: 'Fair Price',  color: '#FFD700', icon: '', diff: 'At market rate' };
    return              { score: 'Overpriced',  color: '#ef4444', icon: '', diff: Math.round((ratio-1)*100) + '% above market' };
  }
};

// ============================================
// PROPERTY RECOMMENDATION ENGINE
// ============================================
const Recommendations = {
  trackView(propId) {
    // Use cached currentUser - this is a sync method called in click handlers
    const user = Auth.currentUser;
    if (!user || !user.email) return;
    const key = 're_viewed_' + user.email;
    let h = [];
    try { h = JSON.parse(localStorage.getItem(key) || '[]'); } catch(e) { h = []; }
    h = [propId, ...h.filter(id => id !== propId)].slice(0, 20);
    try { localStorage.setItem(key, JSON.stringify(h)); } catch(e) {}
  },

  async getSimilar(propId, limit = 3) {
    const all  = await Store.getProperties();
    const prop = all.find(p => p.id === propId);
    if (!prop) return all.slice(0, limit);
    return all
      .filter(p => p.id !== propId)
      .map(p => {
        let s = 0;
        if (p.listingType === prop.listingType) s += 3;
        if (p.bedrooms    === prop.bedrooms)    s += 3;
        if (p.category    === prop.category)    s += 2;
        if (p.city        === prop.city)        s += 4;
        if (prop.price && Math.abs(p.price - prop.price) / prop.price < 0.3) s += 2;
        return { ...p, _score: s };
      })
      .sort((a, b) => b._score - a._score)
      .slice(0, limit);
  },

  async getForUser(limit = 4) {
    // Use cached currentUser for sync context
    const user = Auth.currentUser;
    if (!user || !user.email) {
      const allProps = await Store.getProperties();
      return allProps.slice(0, limit);
    }
    let viewed = [];
    try { viewed = JSON.parse(localStorage.getItem('re_viewed_' + user.email) || '[]'); } catch(e) { viewed = []; }
    if (!viewed.length) {
      const allProps = await Store.getProperties();
      return allProps.slice(0, limit);
    }
    const all    = await Store.getProperties();
    const vProps = viewed.map(id => all.find(p => p.id === id)).filter(Boolean);
    const modeOf = arr => { const f={}; arr.forEach(v=>{f[v]=(f[v]||0)+1;}); return Object.keys(f).sort((a,b)=>f[b]-f[a])[0]; };
    const prefBhk = modeOf(vProps.map(p => p.bedrooms));
    const prefType= modeOf(vProps.map(p => p.listingType));
    const avgP    = vProps.reduce((s,p) => s + p.price, 0) / vProps.length;
    return all
      .filter(p => !viewed.includes(p.id))
      .map(p => {
        let s = 0;
        if (p.bedrooms    === prefBhk)  s += 3;
        if (p.listingType === prefType) s += 3;
        if (avgP && Math.abs(p.price - avgP) / avgP < 0.3) s += 2;
        return { ...p, _score: s };
      })
      .sort((a, b) => b._score - a._score)
      .slice(0, limit);
  }
};

// ============================================
// VIRTUAL TOUR / 360 VIEW
// ============================================
const VirtualTour = {
  open(prop) {
    const ex = document.getElementById('tourModal');
    if (ex) ex.remove();

    const modal = document.createElement('div');
    modal.id = 'tourModal';
    modal.style.cssText = 'position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,0.95);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;';

    const hasVideo = prop.tourVideo;
    const has360   = prop.tour360;
    let content = '';

    if (hasVideo) {
      content = `<video controls autoplay style="max-width:100%;max-height:70vh;border-radius:12px;box-shadow:0 0 60px rgba(255,215,0,0.2);"><source src="${prop.tourVideo}">Your browser does not support video.</video>`;
    } else if (has360) {
      content = `<img src="${prop.tour360}" style="max-width:100%;max-height:70vh;border-radius:12px;object-fit:contain;" alt="360 View">`;
    } else {
      content = `
        <img src="${prop.image || 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800'}" style="max-width:100%;max-height:55vh;border-radius:12px;object-fit:cover;box-shadow:0 0 60px rgba(255,215,0,0.2);">
        <div style="margin-top:14px;padding:12px 18px;background:rgba(255,215,0,0.06);border:1px solid rgba(255,215,0,0.18);border-radius:10px;color:#888;font-size:13px;text-align:center;">
           360 tour not available yet.<br><span style="color:var(--gold);font-size:12px;">Upload a tour video when adding the property.</span>
        </div>`;
    }

    modal.innerHTML = `
      <div style="width:100%;max-width:900px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:19px;font-weight:800;color:#FFD700;">${hasVideo?' Video Walkthrough':has360?' 360 Virtual Tour':' Property Photos'}</div>
            <div style="color:#777;font-size:13px;">${prop.title}</div>
          </div>
          <button onclick="document.getElementById('tourModal').remove()" style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);color:#fff;font-size:22px;width:40px;height:40px;border-radius:50%;cursor:pointer;">&times;</button>
        </div>
        ${content}
      </div>`;

    document.body.appendChild(modal);
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', esc); }
    });
  }
};

// ============================================
// SECURITY FEATURES - EXTENDED
// ============================================

//  1. SESSION TIMEOUT (30 min idle auto-logout) 
const SessionGuard = {
  TIMEOUT_MS: 30 * 60 * 1000, // 30 minutes
  WARNING_MS: 2  * 60 * 1000, // warn 2 min before
  _timer:   null,
  _warnTimer: null,
  _warningShown: false,

  start() {
    // Note: isLoggedIn is async - we start the guard and let individual timeouts check auth
    this.reset();
    ['click','keydown','mousemove','touchstart','scroll'].forEach(ev => {
      document.addEventListener(ev, () => this.reset(), { passive: true });
    });
  },

  reset() {
    clearTimeout(this._timer);
    clearTimeout(this._warnTimer);
    this._warningShown = false;

    // Warning banner 2 min before logout
    this._warnTimer = setTimeout(async () => {
      const logged = await Auth.isLoggedIn();
      if (!logged) return;
      if (this._warningShown) return;
      this._warningShown = true;
      this._showWarning();
    }, this.TIMEOUT_MS - this.WARNING_MS);

    // Auto-logout
    this._timer = setTimeout(async () => {
      const logged = await Auth.isLoggedIn();
      if (!logged) return;
      SecurityLog.add('session_timeout', 'Auto-logged out due to 30 min inactivity');
      showToast('Session expired - please sign in again', 'warning');
      setTimeout(() => Auth.logout(), 1500);
    }, this.TIMEOUT_MS);
  },

  _showWarning() {
    const existing = document.getElementById('sessionWarnBanner');
    if (existing) existing.remove();
    const banner = document.createElement('div');
    banner.id = 'sessionWarnBanner';
    banner.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#1a1200;border:1px solid #e6b94a;color:#e6b94a;padding:12px 20px;border-radius:10px;z-index:9999;font-size:13px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 20px rgba(0,0,0,0.5);animation:fadeUp 0.3s ease;';
    banner.innerHTML = '<span> Session expiring in 2 minutes due to inactivity</span><button onclick="document.getElementById(\'sessionWarnBanner\').remove();SessionGuard.reset();" style="background:#e6b94a;color:#000;border:none;padding:4px 10px;border-radius:5px;cursor:pointer;font-size:12px;font-weight:700;">Stay Logged In</button>';
    document.body.appendChild(banner);
    setTimeout(() => { if (banner.parentNode) banner.remove(); }, 10000);
  },

  stop() {
    clearTimeout(this._timer);
    clearTimeout(this._warnTimer);
    const b = document.getElementById('sessionWarnBanner');
    if (b) b.remove();
  }
};

//  2. DEVICE FINGERPRINT 
const DeviceFingerprint = {
  async get() {
    const parts = [
      navigator.userAgent,
      navigator.language,
      screen.width + 'x' + screen.height,
      screen.colorDepth,
      new Date().getTimezoneOffset(),
      navigator.hardwareConcurrency || 0,
      navigator.platform || ''
    ].join('|');
    // SHA-256 hash of parts
    try {
      const enc  = new TextEncoder().encode(parts);
      const buf  = await crypto.subtle.digest('SHA-256', enc);
      const arr  = Array.from(new Uint8Array(buf));
      return arr.map(b => b.toString(16).padStart(2,'0')).join('').slice(0, 16);
    } catch(e) {
      return btoa(parts).slice(0, 16);
    }
  },

  async checkNewDevice(email) {
    const fp   = await this.get();
    const key  = 're_devices_' + email;
    let known  = [];
    try { known = JSON.parse(localStorage.getItem(key) || '[]'); } catch(e) {}
    if (!known.includes(fp)) {
      known.push(fp);
      localStorage.setItem(key, JSON.stringify(known.slice(-5))); // keep last 5 devices
      return { isNew: true, fingerprint: fp };
    }
    return { isNew: false, fingerprint: fp };
  },

  registerDevice(email, fp) {
    const key  = 're_devices_' + email;
    let known  = [];
    try { known = JSON.parse(localStorage.getItem(key) || '[]'); } catch(e) {}
    if (!known.includes(fp)) {
      known.push(fp);
      localStorage.setItem(key, JSON.stringify(known.slice(-5)));
    }
  }
};

//  3. SECURITY ACTIVITY LOG 
const SecurityLog = {
  MAX_ENTRIES: 20,

  add(event, detail, email) {
    // Use Auth.currentUser (sync cache) - Auth.getUser() is async and cannot be awaited here
    const user = email || Auth.currentUser?.email || 'unknown';
    const key  = 're_seclog_' + user;
    let log = [];
    try { log = JSON.parse(localStorage.getItem(key) || '[]'); } catch(e) {}
    log.unshift({
      event,
      detail: detail || '',
      time: new Date().toISOString(),
      ua: navigator.userAgent.slice(0, 80)
    });
    log = log.slice(0, this.MAX_ENTRIES);
    try { localStorage.setItem(key, JSON.stringify(log)); } catch(e) {}
  },

  getAll(email) {
    const user = email || Auth.currentUser?.email || 'unknown';
    try { return JSON.parse(localStorage.getItem('re_seclog_' + user) || '[]'); } catch(e) { return []; }
  },

  formatTime(iso) {
    try {
      return new Date(iso).toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' });
    } catch(e) { return iso; }
  },

  getIcon(event) {
    const icons = {
      login_success:    '',
      login_failed:     '',
      login_locked:     '',
      logout:           '',
      signup:           '',
      session_timeout:  '',
      password_changed: '',
      new_device:       '',
      profile_updated:  '',
      otp_sent:         '',
      otp_verified:     '',
      otp_failed:       '',
    };
    return icons[event] || '';
  }
};

//  4. RE-AUTH FOR SENSITIVE ACTIONS 
const ReAuth = {
  // Returns a Promise - resolves if password correct, rejects if cancelled/wrong
  require(reason) {
    return new Promise((resolve, reject) => {
      // Use currentUser cache (sync) - Auth.getUser() is async
      const user = Auth.currentUser;
      if (!user) { reject('not_logged_in'); return; }

      const overlay = document.createElement('div');
      overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;padding:20px;animation:fadeUp 0.2s ease;';
      overlay.innerHTML = `
        <div style="background:#131516;border:1px solid rgba(255,215,0,0.2);border-radius:16px;padding:28px;width:100%;max-width:380px;box-shadow:0 20px 60px rgba(0,0,0,0.7);">
          <div style="text-align:center;margin-bottom:20px;">
            <div style="font-size:36px;margin-bottom:8px;"></div>
            <h3 style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#e8e8e8;margin-bottom:6px;">Confirm Your Identity</h3>
            <p style="color:#666;font-size:0.82rem;">${reason || 'Enter your password to continue'}</p>
          </div>
          <div style="margin-bottom:14px;">
            <label style="font-size:0.8rem;color:#888;display:block;margin-bottom:6px;">Password</label>
            <input type="password" id="reAuthPass" placeholder="Enter your password" autocomplete="current-password"
              style="width:100%;padding:11px 14px;background:#0d0f10;border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#e8e8e8;font-size:0.9rem;outline:none;box-sizing:border-box;">
          </div>
          <div id="reAuthErr" style="color:#ef4444;font-size:0.8rem;min-height:18px;margin-bottom:10px;"></div>
          <div style="display:flex;gap:10px;">
            <button id="reAuthCancel" style="flex:1;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#888;cursor:pointer;font-size:0.875rem;">Cancel</button>
            <button id="reAuthConfirm" style="flex:1;padding:10px;background:linear-gradient(135deg,#FFD700,#FFA500);border:none;border-radius:8px;color:#000;font-weight:700;cursor:pointer;font-size:0.875rem;">Confirm</button>
          </div>
        </div>`;

      document.body.appendChild(overlay);
      const passEl    = overlay.querySelector('#reAuthPass');
      const errEl     = overlay.querySelector('#reAuthErr');
      const confirmBtn = overlay.querySelector('#reAuthConfirm');
      const cancelBtn  = overlay.querySelector('#reAuthCancel');

      setTimeout(() => passEl.focus(), 100);

      async function tryAuth() {
        const entered = passEl.value;
        if (!entered) { errEl.textContent = 'Please enter your password'; return; }
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Verifying...';
        const ok = await verifyPassword(entered, user.passwordHash);
        if (ok) {
          overlay.remove();
          resolve(true);
        } else {
          errEl.textContent = 'Incorrect password';
          passEl.value = '';
          passEl.focus();
          confirmBtn.disabled = false;
          confirmBtn.textContent = 'Confirm';
        }
      }

      confirmBtn.addEventListener('click', tryAuth);
      passEl.addEventListener('keypress', e => { if (e.key === 'Enter') tryAuth(); });
      cancelBtn.addEventListener('click', () => { overlay.remove(); reject('cancelled'); });
      overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); reject('cancelled'); } });
    });
  }
};

//  5. REMEMBER ME 
const RememberMe = {
  STORAGE_KEY: 're_remember',
  DURATION_DAYS: 7,

  save(email, remember) {
    if (remember) {
      const expiry = Date.now() + this.DURATION_DAYS * 86400000;
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify({ email, expiry }));
    } else {
      localStorage.removeItem(this.STORAGE_KEY);
    }
  },

  load() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (!raw) return null;
      const data = JSON.parse(raw);
      if (Date.now() > data.expiry) {
        localStorage.removeItem(this.STORAGE_KEY);
        return null;
      }
      return data.email;
    } catch(e) { return null; }
  },

  clear() {
    localStorage.removeItem(this.STORAGE_KEY);
  }
};
window.RememberMe = RememberMe;

//  6. PASSWORD STRENGTH SCORER 
const PasswordStrength = {
  check(pass) {
    let score = 0;
    const checks = {
      length:    pass.length >= 8,
      longPass:  pass.length >= 12,
      upper:     /[A-Z]/.test(pass),
      lower:     /[a-z]/.test(pass),
      number:    /[0-9]/.test(pass),
      special:   /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pass),
      noCommon:  !['password','123456','qwerty','abc123','letmein'].includes(pass.toLowerCase()),
      noRepeat:  !/(.)\1{2,}/.test(pass)
    };
    if (checks.length)   score += 1;
    if (checks.longPass) score += 1;
    if (checks.upper)    score += 1;
    if (checks.lower)    score += 1;
    if (checks.number)   score += 1;
    if (checks.special)  score += 2;
    if (checks.noCommon) score += 1;
    if (checks.noRepeat) score += 1;

    let label, color, pct;
    if (score <= 2)      { label = 'Very Weak';  color = '#ef4444'; pct = 15; }
    else if (score <= 4) { label = 'Weak';        color = '#f97316'; pct = 35; }
    else if (score <= 6) { label = 'Fair';         color = '#e6b94a'; pct = 60; }
    else if (score <= 7) { label = 'Strong';       color = '#22c55e'; pct = 80; }
    else                 { label = 'Very Strong';  color = '#10b981'; pct = 100; }

    return { score, label, color, pct, checks };
  },

  // Attach to a password input and show visual feedback
  attach(inputId, barId, labelId) {
    const input = document.getElementById(inputId);
    const bar   = document.getElementById(barId);
    const lbl   = document.getElementById(labelId);
    if (!input) return;

    input.addEventListener('input', () => {
      const result = this.check(input.value);
      if (bar) {
        bar.style.width     = result.pct + '%';
        bar.style.background = result.color;
        bar.style.transition = 'all 0.3s ease';
      }
      if (lbl) {
        lbl.textContent = input.value ? result.label : '';
        lbl.style.color = result.color;
      }
    });
  }
};

//  7. CLIPBOARD PROTECTION 
const ClipboardGuard = {
  protect(inputId) {
    const el = document.getElementById(inputId);
    if (!el) return;
    el.addEventListener('copy',  e => e.preventDefault());
    el.addEventListener('cut',   e => e.preventDefault());
    el.addEventListener('paste', e => e.preventDefault());
  }
};

//  8. CONTENT SECURITY (Input sanitizer + XSS prevention) 
const InputSecurity = {
  // Strip dangerous HTML tags and attributes
  sanitizeHTML(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  },

  // Validate that a string contains no script injection
  isSafe(str) {
    const dangerous = /<script|javascript:|on\w+\s*=|<iframe|<object|<embed|data:/i;
    return !dangerous.test(str);
  },

  // Limit string length
  truncate(str, max) {
    return String(str || '').slice(0, max);
  }
};

//  9. SECURITY DASHBOARD MODAL 
async function showSecurityDashboard() {
  // Await the async getUser properly
  const user = Auth.currentUser || await Auth.getUser();
  if (!user) { showToast('Please sign in to view security info', 'warning'); return; }

  const log  = SecurityLog.getAll();
  const existing = document.getElementById('secDashModal');
  if (existing) existing.remove();

  const logRows = log.length ? log.slice(0, 5).map(entry => `
    <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
      <span style="font-size:18px;flex-shrink:0">${SecurityLog.getIcon(entry.event)}</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:0.82rem;color:#d0d0d0;font-weight:600">${entry.event.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>
        <div style="font-size:0.75rem;color:#666">${entry.detail}</div>
        <div style="font-size:0.7rem;color:#444;margin-top:2px">${SecurityLog.formatTime(entry.time)}</div>
      </div>
    </div>`).join('') : '<p style="color:#444;font-size:0.82rem;text-align:center;padding:20px 0">No activity recorded yet</p>';

  const modal = document.createElement('div');
  modal.id = 'secDashModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;padding:20px;';
  modal.innerHTML = `
    <div style="background:#131516;border:1px solid rgba(255,215,0,0.15);border-radius:18px;width:100%;max-width:480px;max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.7);">
      <div style="padding:24px 24px 0;position:sticky;top:0;background:#131516;z-index:1;border-bottom:1px solid rgba(255,255,255,0.05);padding-bottom:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#e8e8e8;">🛡️ Security Center</div>
            <div style="font-size:0.75rem;color:#666;margin-top:2px;">Account: ${user.email}</div>
          </div>
          <button onclick="document.getElementById('secDashModal').remove()" style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);color:#fff;width:34px;height:34px;border-radius:50%;cursor:pointer;font-size:18px;">&times;</button>
        </div>
      </div>

      <div style="padding:20px 24px;">

        <!-- Status Cards -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px;">
          <div style="background:#0d1200;border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:12px;">
            <div style="font-size:0.78rem;font-weight:700;color:#22c55e">2FA Active</div>
            <div style="font-size:0.7rem;color:#666">Email OTP on login</div>
          </div>
          <div style="background:#120d00;border:1px solid rgba(230,185,74,0.2);border-radius:10px;padding:12px;">
            <div style="font-size:0.78rem;font-weight:700;color:#e6b94a">SHA-256</div>
            <div style="font-size:0.7rem;color:#666">Password hashed</div>
          </div>
        </div>

        <!-- Active Session Info -->
        <div style="background:#0d0f10;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:14px;margin-bottom:20px;">
          <div style="font-size:0.82rem;font-weight:700;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Current Session</div>
          <div style="font-size:0.8rem;color:#bbb;line-height:1.8;">
            <div> <span style="color:#e8e8e8">${user.fullName || 'User'}</span></div>
            <div> Role: <span id="secDashRoleText" style="color:#e6b94a">${(user.role||'buyer').charAt(0).toUpperCase()+(user.role||'buyer').slice(1)}</span></div>
            <div> Timeout: <span style="color:#e8e8e8">30 min inactivity</span></div>
          </div>
        </div>

        <!-- RBAC ROLE SIMULATOR -->
        <div style="background:#0d0f10;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:14px;margin-bottom:20px;">
          <div style="font-size:0.82rem;font-weight:700;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">RBAC Role Simulator</div>
          <div style="display:flex;align-items:center;gap:10px;">
            <select id="rbacRoleSimulator" onchange="simulateUserRole(this.value)" style="flex:1;padding:8px;background:#1a1c1e;border:1px solid rgba(255,255,255,0.15);border-radius:6px;color:#fff;font-size:0.8rem;outline:none;">
              <option value="buyer">Buyer (No CSV access)</option>
              <option value="seller">Seller (No CSV access)</option>
              <option value="agent">Agent (Has CSV access)</option>
              <option value="admin">Admin (Has CSV access)</option>
            </select>
          </div>
        </div>

        <!-- API CREDENTIALS ENCRYPTION -->
        <div style="background:#0d0f10;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:14px;margin-bottom:20px;">
          <div style="font-size:0.82rem;font-weight:700;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">API Credentials Encryption</div>
          <div id="integrationStatus" style="font-size:0.75rem;color:#aaa;margin-bottom:10px;line-height:1.4;">
            Loading integrations...
          </div>
          <div style="display:flex;gap:10px;">
            <button onclick="seedIntegrations()" class="btn btn-outline btn-sm" style="font-size:0.72rem;padding:4px 8px;cursor:pointer;">Seed Integrations</button>
            <button onclick="runEncryptionMigration()" class="btn btn-gold btn-sm" style="font-size:0.72rem;padding:4px 8px;cursor:pointer;">Run Migration</button>
          </div>
        </div>

        <!-- WEBHOOKS & EVENT DISPATCH -->
        <div style="background:#0d0f10;border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:14px;margin-bottom:20px;">
          <div style="font-size:0.82rem;font-weight:700;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Webhooks & Event Dispatch</div>
          <div id="webhookLogsContainer" style="font-size:0.75rem;color:#aaa;margin-bottom:10px;line-height:1.4;">
            Loading webhook logs...
          </div>
          <div style="display:flex;gap:10px;">
            <button onclick="simulateInboundWebhook()" class="btn btn-gold btn-sm" style="font-size:0.72rem;padding:4px 8px;cursor:pointer;">Simulate Inbound Webhook</button>
            <button onclick="loadWebhookLogs()" class="btn btn-outline btn-sm" style="font-size:0.72rem;padding:4px 8px;cursor:pointer;">Refresh Logs</button>
          </div>
        </div>

        <!-- Activity Log -->
        <div style="font-size:0.82rem;font-weight:700;color:#888;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Recent Activity</div>
        <div>${logRows}</div>

        <!-- Actions -->
        <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;">
          <a href="profile.html" onclick="document.getElementById('secDashModal').remove()" style="flex:1;min-width:120px;padding:10px;background:rgba(230,185,74,0.1);border:1px solid rgba(230,185,74,0.3);border-radius:8px;color:#e6b94a;text-align:center;text-decoration:none;font-size:0.82rem;font-weight:600;"> Change Password</a>
          <button onclick="if(confirm('Sign out from all sessions?')){SecurityLog.add('logout','Manual logout');Auth.logout();}" style="flex:1;min-width:120px;padding:10px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;color:#ef4444;cursor:pointer;font-size:0.82rem;font-weight:600;"> Sign Out</button>
        </div>
      </div>
    </div>`;

  document.body.appendChild(modal);
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

  const rbacSelector = document.getElementById('rbacRoleSimulator');
  if (rbacSelector) rbacSelector.value = user.role || 'buyer';

  loadIntegrationsList();
  loadWebhookLogs();
}

async function simulateUserRole(newRole) {
  if (Auth.currentUser) {
    Auth.currentUser.role = newRole;
  }
  const storedUser = localStorage.getItem('supabase_user') || localStorage.getItem('user');
  if (storedUser) {
    try {
      const parsed = JSON.parse(storedUser);
      parsed.role = newRole;
      localStorage.setItem('supabase_user', JSON.stringify(parsed));
      localStorage.setItem('user', JSON.stringify(parsed));
    } catch(e){}
  }
  showToast(`Simulating role: ${newRole.toUpperCase()}`, 'success');
  const welcome = document.getElementById('welcomeMsg');
  if (welcome) {
    welcome.textContent = 'Welcome back, ' + (Auth.currentUser?.fullName || 'User') + ` (${newRole})`;
  }
  const roleSpan = document.getElementById('secDashRoleText');
  if (roleSpan) {
    roleSpan.textContent = newRole.charAt(0).toUpperCase() + newRole.slice(1);
  }
}

async function seedIntegrations() {
  try {
    const res = await fetch('http://localhost:3001/api/seed-integrations', { method: 'POST' }); // wait, or seed-integrations route path? Let's check: we defined `/api/admin/seed-integrations`
    const res2 = await fetch('http://localhost:3001/api/admin/seed-integrations', { method: 'POST' });
    const data = await res2.json();
    showToast(data.message || 'Integrations seeded!', 'success');
    await loadIntegrationsList();
  } catch (err) {
    showToast('Failed to seed: ' + err.message, 'error');
  }
}

async function runEncryptionMigration() {
  try {
    const res = await fetch('http://localhost:3001/api/admin/migrate-encrypt', { method: 'POST' });
    const data = await res.json();
    showToast(`${data.message} Migrated: ${data.migrated}, Skipped: ${data.skipped}`, 'success');
    await loadIntegrationsList();
  } catch (err) {
    showToast('Migration failed: ' + err.message, 'error');
  }
}

async function loadIntegrationsList() {
  const container = document.getElementById('integrationStatus');
  if (!container) return;
  try {
    const res = await fetch('http://localhost:3001/api/admin/integrations');
    const data = await res.json();
    if (!data || data.length === 0) {
      container.innerHTML = '<div style="color:#666">No integrations seeded. Click "Seed Integrations" below.</div>';
      return;
    }
    
    let html = '<div style="display:flex;flex-direction:column;gap:8px;max-height:150px;overflow-y:auto;padding-right:4px;">';
    data.forEach(item => {
      const lockIcon = item.isEncrypted ? '🔒 <span style="color:#22c55e;font-weight:700;">Encrypted</span>' : '🔓 <span style="color:#f59e0b;">Plaintext (Vulnerable)</span>';
      const displayCreds = JSON.stringify(item.decryptedValue);
      const rawCreds = JSON.stringify(item.rawPayload);
      html += `
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);padding:8px;border-radius:6px;font-size:0.72rem;line-height:1.4;">
          <div style="display:flex;justify-content:space-between;font-weight:700;color:#e8e8e8;margin-bottom:4px;">
            <span>${item.source}</span>
            <span style="font-size:0.65rem;margin-left:auto;">${lockIcon}</span>
          </div>
          <div style="color:#666;font-family:monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title='Raw DB: ${rawCreds}'>
            <strong>Raw:</strong> ${rawCreds}
          </div>
          <div style="color:#e6b94a;font-family:monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title='Decrypted: ${displayCreds}'>
            <strong>Decrypted:</strong> ${displayCreds}
          </div>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color:#ef4444">Error loading integrations: ${err.message}</div>`;
  }
}

async function simulateInboundWebhook() {
  const secret = '7f5c71b12b591b61c10d3f8206d9d1c9ef00192e2124508de8a3b83981881882';
  const payload = {
    event: 'property.created',
    data: {
      title: 'Webhook Luxury Estate ' + Math.floor(Math.random() * 1000),
      price: 1500000,
      location: 'Miami Beach, USA',
      sqft: 2800,
      image: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600',
      type: 'sale',
      featured: true
    }
  };
  const jsonStr = JSON.stringify(payload);
  try {
    const signature = await computeHmacSha256(jsonStr, secret);
    const res = await fetch('http://localhost:3001/api/webhooks/property', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-realestate-signature': signature
      },
      body: jsonStr
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Inbound webhook received: ' + JSON.stringify(data), 'success');
    } else {
      showToast('Webhook rejected: ' + data.error, 'error');
    }
    await loadWebhookLogs();
  } catch (err) {
    showToast('Webhook simulation failed: ' + err.message, 'error');
  }
}

async function computeHmacSha256(message, secret) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);
  const key = await window.crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await window.crypto.subtle.sign(
    "HMAC",
    key,
    messageData
  );
  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

async function loadWebhookLogs() {
  const container = document.getElementById('webhookLogsContainer');
  if (!container) return;
  try {
    const res = await fetch('http://localhost:3001/api/admin/webhooks/logs');
    const data = await res.json();
    if (!data || data.length === 0) {
      container.innerHTML = '<div style="color:#666">No webhook activity logged yet. Try simulating an inbound webhook or seeding listings to trigger outbound hooks.</div>';
      return;
    }
    let html = '<div style="display:flex;flex-direction:column;gap:8px;max-height:150px;overflow-y:auto;padding-right:4px;">';
    data.forEach(log => {
      const isOut = log.direction === 'outbound';
      const arrow = isOut ? '➡️ OUTBOUND' : '⬅️ INBOUND';
      const arrowColor = isOut ? '#3b82f6' : '#22c55e';
      const statusColor = log.status === 'success' ? '#22c55e' : '#ef4444';
      const payloadStr = JSON.stringify(log.payload);
      html += `
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);padding:8px;border-radius:6px;font-size:0.72rem;line-height:1.4;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:${arrowColor};font-weight:700;">${arrow}</span>
            <span style="color:#888;">${log.event}</span>
            <span style="color:${statusColor};font-weight:700;margin-left:auto;">${log.status.toUpperCase()}</span>
          </div>
          <div style="color:#666;font-family:monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title='Payload: ${payloadStr}'>
            <strong>Payload:</strong> ${payloadStr}
          </div>
          <div style="color:#444;font-size:0.65rem;margin-top:2px;">
            ${new Date(log.timestamp).toLocaleTimeString()}
          </div>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color:#ef4444">Error loading webhook logs: ${err.message}</div>`;
  }
}

async function exportPropertiesCSV() {
  try {
    const user = Auth.currentUser || await Auth.getUser();
    const role = user?.role || 'buyer';
    window.open(`http://localhost:3001/api/properties/csv?role=${role}`, '_blank');
  } catch (err) {
    console.error("CSV Export failed:", err);
    window.open('http://localhost:3001/api/properties/csv?role=buyer', '_blank');
  }
}

//  AUTO-START SessionGuard, Sidebar & Tooltips on every page
document.addEventListener('DOMContentLoaded', async () => {
  initSidebar();
  // Initialise tooltip system (from tooltip.js) with MutationObserver so
  // dynamically rendered rows (property-catalog table) also get tooltips.
  if (typeof tooltipObserver === 'function') tooltipObserver();
  const logged = await Auth.isLoggedIn();
  if (logged) {
    SessionGuard.start();
  }
});