const crypto = require("crypto");

const ALGORITHM  = "aes-256-gcm";
const IV_LENGTH  = 12;  // 96-bit IV, standard for AES-GCM
const TAG_LENGTH = 16;

// ─── Hardcoded fallback key (used when env var is missing) ───────────────────
const FALLBACK_KEY = "64392094857410293847561029384756102938475610293847561029384756ab";

/**
 * Resolve the encryption key for a given service.
 * Priority:
 *   1. process.env.TWILIO_ENC_KEY  (if service = 'twilio')
 *   2. process.env.CREDENTIALS_ENCRYPTION_KEY  (global fallback)
 *   3. Hardcoded FALLBACK_KEY  (dev-only last resort)
 *
 * Also accepts a raw 64-char hex string directly (backward-compatible).
 */
function resolveKey(serviceOrHexKey) {
  if (!serviceOrHexKey) {
    return process.env.CREDENTIALS_ENCRYPTION_KEY || FALLBACK_KEY;
  }
  // If caller passed a 64-char hex string directly → use it as-is (old API)
  if (/^[0-9a-fA-F]{64}$/.test(serviceOrHexKey)) {
    return serviceOrHexKey;
  }
  // Treat as a service name → look up per-service env var
  const envVar = `${serviceOrHexKey.toUpperCase()}_ENC_KEY`;
  return process.env[envVar]
      || process.env.CREDENTIALS_ENCRYPTION_KEY
      || FALLBACK_KEY;
}

/**
 * Parse a hex key string into a 32-byte Buffer.
 */
function parseKey(hexKey) {
  if (!hexKey || hexKey.length !== 64) {
    throw new Error(
      "Encryption key must be a 64-character hex string (32 bytes). " +
      `Got length ${hexKey ? hexKey.length : 0}.`
    );
  }
  return Buffer.from(hexKey, "hex");
}

/**
 * Encrypt a plain object using AES-256-GCM.
 *
 * @param {object} plainObj    - The credential object to encrypt
 * @param {string} serviceOrHexKey - Service name ('twilio') OR 64-char hex key string
 * @returns {{ iv, authTag, ciphertext }} - All three components stored separately
 */
function encryptCredentials(plainObj, serviceOrHexKey) {
  const hexKey = resolveKey(serviceOrHexKey);
  const key    = parseKey(hexKey);
  const iv     = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  const plaintext = JSON.stringify(plainObj);
  const encrypted = Buffer.concat([
    cipher.update(plaintext, "utf8"),
    cipher.final(),
  ]);
  const authTag = cipher.getAuthTag();

  return {
    iv:         iv.toString("base64"),
    authTag:    authTag.toString("base64"),  // field renamed: 'tag' → 'authTag' for clarity
    ciphertext: encrypted.toString("base64"),
  };
}

/**
 * Decrypt an encrypted payload back to a plain object using AES-256-GCM.
 *
 * @param {{ iv, authTag, ciphertext } | { iv, tag, ciphertext }} payload
 * @param {string} serviceOrHexKey
 * @returns {object}
 */
function decryptCredentials(payload, serviceOrHexKey) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid encrypted credentials payload — expected an object.");
  }

  // Support both 'authTag' (new) and 'tag' (legacy field name)
  const { iv, ciphertext } = payload;
  const authTag = payload.authTag || payload.tag;

  if (!iv || !authTag || !ciphertext) {
    throw new Error(
      "Invalid encrypted credentials payload — missing iv, authTag/tag, or ciphertext."
    );
  }

  const hexKey   = resolveKey(serviceOrHexKey);
  const key      = parseKey(hexKey);
  const decipher = crypto.createDecipheriv(
    ALGORITHM,
    key,
    Buffer.from(iv, "base64")
  );
  decipher.setAuthTag(Buffer.from(authTag, "base64"));

  const decrypted = Buffer.concat([
    decipher.update(Buffer.from(ciphertext, "base64")),
    decipher.final(),
  ]);

  return JSON.parse(decrypted.toString("utf8"));
}

/**
 * Check if a value looks like an encrypted payload (vs plain object).
 * Accepts both old { iv, tag, ciphertext } and new { iv, authTag, ciphertext }.
 */
function isEncryptedPayload(payload) {
  return (
    !!payload &&
    typeof payload === "object" &&
    "iv"         in payload &&
    "ciphertext" in payload &&
    ("authTag" in payload || "tag" in payload)
  );
}

/**
 * Generate a masked preview of a credential value for display.
 * Input:  { apiKey: "sk_live_abcdefghij1234" }
 * Output: "sk_live_••••••••••1234"
 */
function maskCredential(plainObj) {
  try {
    const vals = Object.values(plainObj);
    if (!vals.length) return "••••••••••";
    const raw = String(vals[0]);
    if (raw.length <= 8) return "••••••••";
    const visible = raw.slice(-4);
    const masked  = "•".repeat(Math.min(raw.length - 4, 14));
    const prefix  = raw.match(/^[a-zA-Z0-9_-]+_/)?.[0] || "";
    return prefix
      ? `${prefix}${masked}${visible}`
      : `${masked}${visible}`;
  } catch {
    return "••••••••••";
  }
}

module.exports = {
  encryptCredentials,
  decryptCredentials,
  isEncryptedPayload,
  maskCredential,
  resolveKey,
};
