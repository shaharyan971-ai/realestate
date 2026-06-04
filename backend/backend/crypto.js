const crypto = require("crypto");

const ALGORITHM = "aes-256-gcm";
const IV_LENGTH = 12; // Standard IV length for AES-GCM is 12 bytes (96 bits)
const TAG_LENGTH = 16;

function parseKey(hexKey) {
  if (!hexKey || hexKey.length !== 64) {
    throw new Error(
      "CREDENTIALS_ENCRYPTION_KEY must be a 64-character hex string (32 bytes)"
    );
  }
  return Buffer.from(hexKey, "hex");
}

/**
 * Encrypt a plain object using AES-256-GCM.
 * The key must be a 64-character hex string (32 bytes).
 */
function encryptCredentials(plainObj, hexKey) {
  const key = parseKey(hexKey);
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  const plaintext = JSON.stringify(plainObj);
  const encrypted = Buffer.concat([
    cipher.update(plaintext, "utf8"),
    cipher.final(),
  ]);
  const tag = cipher.getAuthTag();

  return {
    iv: iv.toString("base64"),
    tag: tag.toString("base64"),
    ciphertext: encrypted.toString("base64"),
  };
}

/**
 * Decrypt an EncryptedPayload back to a plain object using AES-256-GCM.
 */
function decryptCredentials(payload, hexKey) {
  if (
    !payload ||
    typeof payload !== "object" ||
    !("iv" in payload) ||
    !("tag" in payload) ||
    !("ciphertext" in payload)
  ) {
    throw new Error("Invalid encrypted credentials payload");
  }
  const { iv, tag, ciphertext } = payload;

  const key = parseKey(hexKey);
  const decipher = crypto.createDecipheriv(
    ALGORITHM,
    key,
    Buffer.from(iv, "base64")
  );
  decipher.setAuthTag(Buffer.from(tag, "base64"));

  const decrypted = Buffer.concat([
    decipher.update(Buffer.from(ciphertext, "base64")),
    decipher.final(),
  ]);

  return JSON.parse(decrypted.toString("utf8"));
}

/**
 * Check if a payload looks like it's already encrypted (vs plaintext JSON).
 */
function isEncryptedPayload(payload) {
  return (
    !!payload &&
    typeof payload === "object" &&
    "iv" in payload &&
    "tag" in payload &&
    "ciphertext" in payload
  );
}

module.exports = {
  encryptCredentials,
  decryptCredentials,
  isEncryptedPayload
};
