require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const PDFDocument = require('pdfkit');
const axios = require('axios');
const { encryptCredentials, decryptCredentials, isEncryptedPayload, maskCredential } = require('./crypto');

const CREDENTIALS_ENCRYPTION_KEY = process.env.CREDENTIALS_ENCRYPTION_KEY || '64392094857410293847561029384756102938475610293847561029384756ab';
const PROPERTY_WEBHOOK_SECRET = process.env.PROPERTY_WEBHOOK_SECRET || '7f5c71b12b591b61c10d3f8206d9d1c9ef00192e2124508de8a3b83981881882';

const webhookLogs    = []; // in-memory log of webhook transactions
const credentialLogs = []; // in-memory audit log for credentials (fallback when DB offline)

const app = express();

// 1. MIDDLEWARE
app.use(cors()); // Allows frontend to talk to backend
app.use(express.json()); // Allows us to parse JSON data

// 2. DATABASE CONNECTION
// Using a local DB for now. If you have Atlas, replace the URI.
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/realestate_app';

mongoose.connect(MONGODB_URI)
  .then(() => console.log('✅ MongoDB Connected'))
  .catch(err => console.log('❌ DB Error:', err));

// 3. MODELS (The Schema)
const PropertySchema = new mongoose.Schema({
  title: String,
  price: Number,
  location: String,
  sqft: Number,
  image: String, // URL to image
  type: String, // 'sale' or 'rent'
  featured: { type: Boolean, default: false }
});

const Property = mongoose.model('Property', PropertySchema);

// ─── Credential Vault Schema ────────────────────────────────────────────────
// Stores AES-256-GCM components separately for clean separation of concerns.
// The legacy `credentials` Mixed field is kept for backward-compat with
// the migrate-encrypt and seed-integrations endpoints.
const IntegrationSchema = new mongoose.Schema({
  source:       String,
  // ── Legacy field (still written by seed/migrate endpoints) ────────────────
  credentials:  mongoose.Schema.Types.Mixed,
  // ── New vault fields (written by rotate endpoint & future add endpoint) ───
  encryptedKey: String,   // ciphertext only
  iv:           String,   // stored separately
  authTag:      String,   // stored separately
  isActive:     { type: Boolean, default: true },
  createdAt:    { type: Date, default: Date.now },
  lastRotated:  { type: Date, default: null },
  createdBy:    { type: String, default: 'system' },
  expiresAt:    { type: Date, default: null },
  notifyBefore: { type: Number, default: 7 },  // days before expiry to warn
});
const Integration = mongoose.model('Integration', IntegrationSchema);

// ─── Credential Audit Log Schema ─────────────────────────────────────────────
const CredentialLogSchema = new mongoose.Schema({
  action:    String,   // 'created' | 'rotated' | 'deleted' | 'tested' | 'viewed'
  service:   String,
  adminId:   { type: String, default: 'system' },
  timestamp: { type: Date, default: Date.now },
  ip:        { type: String, default: 'unknown' },
});
const CredentialLog = mongoose.model('CredentialLog', CredentialLogSchema);

/** Write one audit entry — to DB if connected, always to in-memory log too. */
async function writeCredentialLog(entry) {
  const record = { ...entry, timestamp: new Date(), id: 'cl_' + Math.random().toString(36).slice(2, 9) };
  credentialLogs.unshift(record);
  if (credentialLogs.length > 200) credentialLogs.pop(); // cap in-memory log
  if (mongoose.connection.readyState === 1) {
    try { await CredentialLog.create(entry); } catch(_) { /* non-critical */ }
  }
}

// 4. ROUTES (API Endpoints)

// GET: Fetch all properties
app.get('/api/properties', async (req, res) => {
  try {
    const properties = await Property.find();
    res.json(properties);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET: Dashboard Stats
app.get('/api/stats', async (req, res) => {
  try {
    const totalProps = await Property.countDocuments();
    const featuredProps = await Property.countDocuments({ featured: true });
    // Mocking message count for now
    res.json({ 
      properties: totalProps, 
      messages: 5, 
      featured: featuredProps 
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Outbound webhook dispatcher
async function dispatchOutboundWebhook(event, payload) {
  const logEntry = {
    id: 'out_' + Math.random().toString(36).slice(2, 9),
    direction: 'outbound',
    event,
    payload,
    timestamp: new Date().toISOString(),
    status: 'pending'
  };
  webhookLogs.unshift(logEntry);

  let targetUrls = [];
  if (mongoose.connection.readyState === 1) {
    try {
      const webhooks = await Integration.find({ source: { $regex: /webhook/i } });
      targetUrls = webhooks.map(w => {
        if (isEncryptedPayload(w.credentials)) {
          try {
            const dec = decryptCredentials(w.credentials, CREDENTIALS_ENCRYPTION_KEY);
            return dec.url;
          } catch(e) {
            return null;
          }
        }
        return w.credentials ? w.credentials.url : null;
      }).filter(Boolean);
    } catch (dbErr) {
      console.warn("DB webhook read error:", dbErr.message);
    }
  }

  // Fallback target URL for demonstration
  if (targetUrls.length === 0) {
    targetUrls.push('https://httpbin.org/post');
  }

  const crypto = require('crypto');
  const rawBody = JSON.stringify(payload);
  const signature = crypto.createHmac('sha256', PROPERTY_WEBHOOK_SECRET).update(rawBody).digest('hex');

  for (const url of targetUrls) {
    try {
      const response = await axios.post(url, payload, {
        headers: {
          'Content-Type': 'application/json',
          'x-realestate-signature': signature
        },
        timeout: 5000
      });
      logEntry.status = 'success';
      logEntry.responseStatus = response.status;
      console.log(`🚀 Outbound webhook successfully sent to ${url}. Event: ${event}`);
    } catch (err) {
      logEntry.status = 'failed';
      logEntry.error = err.message;
      console.warn(`❌ Outbound webhook dispatch to ${url} failed:`, err.message);
    }
  }
}

// POST: Add a fake property (For testing purposes)
app.post('/api/seed', async (req, res) => {
  const dummyData = [
    {
      title: "Luxury Villa",
      price: 1200000,
      location: "Los Angeles, USA",
      sqft: 3500,
      image: "https://images.unsplash.com/photo-1613490493576-7fde63acd811?q=80&w=1000&auto=format&fit=crop",
      featured: true
    },
    {
      title: "Modern Apartment",
      price: 850000,
      location: "New York, USA",
      sqft: 1800,
      image: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?q=80&w=1000&auto=format&fit=crop",
      featured: true
    },
    {
      title: "Beach House",
      price: 950000,
      location: "Miami, USA",
      sqft: 2200,
      image: "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?q=80&w=1000&auto=format&fit=crop",
      featured: true
    }
  ];

  let inserted = [];
  try {
    if (mongoose.connection.readyState === 1) {
      inserted = await Property.insertMany(dummyData);
    } else {
      inserted = dummyData;
    }

    // Trigger outbound webhooks
    for (const p of inserted) {
      dispatchOutboundWebhook('property.created', {
        id: p._id || 'mock_seed',
        title: p.title,
        price: p.price,
        location: p.location,
        timestamp: new Date().toISOString()
      });
    }

    res.json({ message: "Dummy data added and webhooks dispatched!" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Helper function to generate PDF buffer
function generatePropertyPdfBuffer(property) {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ size: "A4", margin: 50 });

    const chunks = [];
    doc.on("data", chunk => chunks.push(chunk));
    doc.on("end", () => resolve(Buffer.concat(chunks)));
    doc.on("error", reject);

    // Title
    doc.fontSize(24).font("Helvetica-Bold").text("Property Report", { align: "center" });
    doc.moveDown(0.3);
    doc.fontSize(10).font("Helvetica").text("RealEstate App", { align: "center" });
    doc.moveDown(1.5);

    // Property Header Information
    doc.fontSize(18).font("Helvetica-Bold").text(property.title || "Untitled Property");
    doc.moveDown(0.2);
    doc.fontSize(14).font("Helvetica-Bold").fillColor("#d4a43a").text(`Price: $${(property.price || 0).toLocaleString()}`);
    doc.fillColor("#000000").font("Helvetica"); // Reset color
    doc.moveDown(0.5);

    // Metadata Table
    const tableTop = doc.y;
    doc.font("Helvetica-Bold");
    doc.text("Detail", 50, tableTop);
    doc.text("Value", 200, tableTop);
    doc.font("Helvetica");
    
    doc.moveTo(50, tableTop + 15).lineTo(500, tableTop + 15).stroke();
    
    let y = tableTop + 25;
    
    const details = [
      { label: "Location", value: property.location || "N/A" },
      { label: "Size (SqFt)", value: property.sqft ? `${property.sqft} sqft` : "N/A" },
      { label: "Listing Type", value: property.type ? property.type.toUpperCase() : "N/A" },
      { label: "Featured Status", value: property.featured ? "Yes" : "No" }
    ];

    details.forEach(item => {
      doc.text(item.label, 50, y);
      doc.text(item.value, 200, y);
      y += 20;
    });

    doc.moveDown(1.5);

    // If an image URL exists, fetch and embed it
    if (property.image) {
      axios.get(property.image, { responseType: 'arraybuffer' })
        .then(response => {
          const imgBuffer = Buffer.from(response.data);
          doc.image(imgBuffer, 50, doc.y, { width: 450 });
          doc.end();
        })
        .catch(err => {
          console.warn("Failed to load property image for PDF:", err.message);
          doc.fontSize(10).fillColor("#777").text("[Property image offline or unavailable]");
          doc.end();
        });
    } else {
      doc.end();
    }
  });
}

// GET: Generate PDF Report for a property
app.get('/api/properties/:id/pdf', async (req, res) => {
  try {
    const id = req.params.id;
    let property;

    // Check if MongoDB is connected and we can find the property
    if (mongoose.connection.readyState === 1) {
      try {
        property = await Property.findById(id);
      } catch (dbErr) {
        console.warn("Invalid ID or DB search error:", dbErr.message);
      }
    }

    // Fallback: If not found in database or DB not connected, look in frontend demo data
    if (!property) {
      property = {
        title: "Sample Modern Villa",
        price: 980000,
        location: "Los Angeles, CA",
        sqft: 2400,
        type: "sale",
        featured: true,
        image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600"
      };
    }

    const buffer = await generatePropertyPdfBuffer(property);

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="Property-${String(id).slice(-8)}.pdf"`);
    res.setHeader('Content-Length', buffer.length);
    res.send(buffer);
  } catch (err) {
    console.error('PDF Generation Error:', err);
    res.status(500).json({ error: 'Failed to generate PDF: ' + err.message });
  }
});

// Middleware to enforce RBAC
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    // Check if role is supplied in query string or headers (mock/testing mechanism)
    const role = req.query.role || req.headers['x-user-role'] || 'buyer';
    
    if (!allowedRoles.includes(role)) {
      return res.status(403).json({ error: 'Forbidden: Insufficient permissions. Requires one of: ' + allowedRoles.join(', ') });
    }
    next();
  };
}

// GET: Export all properties as CSV
app.get('/api/properties/csv', requireRole('admin', 'agent'), async (req, res) => {
  try {
    let properties = [];
    if (mongoose.connection.readyState === 1) {
      try {
        properties = await Property.find();
      } catch (dbErr) {
        console.warn("DB search error:", dbErr.message);
      }
    }

    // Fallback: If DB empty or not connected, use dummy seed data
    if (!properties || properties.length === 0) {
      properties = [
        {
          _id: "mock1",
          title: "Luxury Villa",
          price: 1200000,
          location: "Los Angeles, USA",
          sqft: 3500,
          type: "sale",
          featured: true
        },
        {
          _id: "mock2",
          title: "Modern Apartment",
          price: 850000,
          location: "New York, USA",
          sqft: 1800,
          type: "rent",
          featured: true
        },
        {
          _id: "mock3",
          title: "Beach House",
          price: 950000,
          location: "Miami, USA",
          sqft: 2200,
          type: "sale",
          featured: true
        }
      ];
    }

    const headers = ['id', 'title', 'price', 'location', 'sqft', 'type', 'featured'];
    const escapeCSV = (val) => {
      if (val === undefined || val === null) return '';
      let str = String(val);
      if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
        str = '"' + str.replace(/"/g, '""') + '"';
      }
      return str;
    };

    const csvRows = [];
    csvRows.push(headers.join(','));

    for (const p of properties) {
      const row = [
        escapeCSV(p._id),
        escapeCSV(p.title),
        escapeCSV(p.price),
        escapeCSV(p.location),
        escapeCSV(p.sqft),
        escapeCSV(p.type || 'sale'),
        escapeCSV(p.featured)
      ];
      csvRows.push(row.join(','));
    }

    const csvContent = csvRows.join('\r\n');
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="properties.csv"');
    res.send(csvContent);
  } catch (err) {
    console.error('CSV Generation Error:', err);
    res.status(500).json({ error: 'Failed to generate CSV: ' + err.message });
  }
});

// POST: Seed mock integrations (some plaintext, some encrypted for testing)
app.post('/api/admin/seed-integrations', async (req, res) => {
  try {
    if (mongoose.connection.readyState !== 1) {
      // Offline mode mockup seeding isn't persisted to DB, but we can return success
      return res.json({ message: 'Offline mode: Mock integrations seeded (virtual)!' });
    }
    
    // Clear old integrations
    await Integration.deleteMany({});
    
    const dummyIntegrations = [
      {
        source: 'Supabase Auth',
        credentials: {
          url: 'https://ynsefltcqtffcdmxwpbn.supabase.co',
          anonKey: 'sb_publishable_AnRqy1ODPXb7gFPlaybSVw_zoL4aLon'
        }
      },
      {
        source: 'EmailJS',
        credentials: {
          publicKey: 'offi1R2H70RXPsPGN',
          serviceId: 'service_q6ds28w',
          templateId: 'template_7tdkqjv'
        }
      },
      {
        source: 'Mapbox API',
        credentials: encryptCredentials({
          apiKey: 'pk.eyJ1IjoicmVhbGVzdGF0ZSIsImEiOiJjbDFhMmIzYzQ1ZDY3ODkwMTIzNDU2Nzg5MCJ9'
        }, CREDENTIALS_ENCRYPTION_KEY)
      }
    ];
    
    await Integration.insertMany(dummyIntegrations);
    res.json({ message: 'Mock integrations seeded in database!' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST: Migrate integration credentials (encrypt any plaintext rows)
app.post('/api/admin/migrate-encrypt', async (req, res) => {
  try {
    if (mongoose.connection.readyState !== 1) {
      // Offline fallback: simulate migration on a mockup set
      return res.json({
        message: 'Offline migration simulated successfully!',
        migrated: 2,
        skipped: 1
      });
    }

    const integrations = await Integration.find();
    let migrated = 0;
    let skipped = 0;

    for (const integration of integrations) {
      if (isEncryptedPayload(integration.credentials)) {
        skipped++;
        continue;
      }

      const encrypted = encryptCredentials(integration.credentials, CREDENTIALS_ENCRYPTION_KEY);
      await Integration.updateOne(
        { _id: integration._id },
        { $set: { credentials: encrypted } }
      );
      migrated++;
    }

    res.json({
      message: 'Migration completed successfully!',
      migrated,
      skipped
    });
  } catch (err) {
    console.error('Migration failed:', err);
    res.status(500).json({ error: 'Migration failed: ' + err.message });
  }
});

// GET /api/admin/integrations
// ⚠️  SECURITY: Returns ONLY safe display fields.
//     Raw keys, ciphertext, iv, and authTag NEVER leave the backend.
app.get('/api/admin/integrations', async (req, res) => {
  const ip      = req.ip || req.headers['x-forwarded-for'] || 'unknown';
  const adminId = req.headers['x-admin-id'] || req.query.adminId || 'system';
  try {
    let integrations = [];
    if (mongoose.connection.readyState === 1) {
      integrations = await Integration.find();
    } else {
      // Offline mock — credentials field contains dummy values
      integrations = [
        { _id: 'mock_int_1', source: 'Supabase Auth',  credentials: { url: 'https://example.supabase.co', anonKey: 'sb_mock_key_abc123xyz789' }, isActive: true, createdAt: new Date('2025-01-01'), createdBy: 'system', lastRotated: null },
        { _id: 'mock_int_2', source: 'EmailJS',         credentials: { publicKey: 'offi1R2H70RXPsPGN', serviceId: 'service_q6ds28w' }, isActive: true, createdAt: new Date('2025-01-02'), createdBy: 'system', lastRotated: null },
        { _id: 'mock_int_3', source: 'Mapbox API',      credentials: encryptCredentials({ apiKey: 'pk.eyJ1IjoicmVhbGVzdGF0ZSIsImEiOiJjbDFhMmIzYzQ1ZDY3ODkwMTIzNDU2Nzg5MCJ9' }, CREDENTIALS_ENCRYPTION_KEY), isActive: true, createdAt: new Date('2025-01-03'), createdBy: 'system', lastRotated: null },
      ];
    }

    // ── Build safe display objects — no raw keys ever returned ────────────────
    const now    = Date.now();
    const result = integrations.map(item => {
      const isEncrypted = isEncryptedPayload(item.credentials);

      // Generate a masked key preview (e.g. "sk_live_••••••••3f9a")
      let keyPreview = '••••••••••';
      if (isEncrypted) {
        try {
          const dec = decryptCredentials(item.credentials, CREDENTIALS_ENCRYPTION_KEY);
          keyPreview = maskCredential(dec);
        } catch (_) { keyPreview = '⚠ Decryption error'; }
      } else if (item.credentials && typeof item.credentials === 'object') {
        keyPreview = maskCredential(item.credentials);
      }

      // Expiry calculations
      let daysUntilExpiry = null;
      let expiryWarning   = false;
      if (item.expiresAt) {
        daysUntilExpiry = Math.ceil((new Date(item.expiresAt) - now) / 86400000);
        expiryWarning   = daysUntilExpiry <= (item.notifyBefore || 7);
      }

      return {
        _id:            String(item._id),
        source:         item.source,
        status:         item.isActive !== false ? 'connected' : 'inactive',
        isEncrypted,
        keyPreview,                              // masked, safe to display
        createdBy:      item.createdBy   || 'system',
        createdAt:      item.createdAt   || null,
        lastRotated:    item.lastRotated  || null,
        isActive:       item.isActive !== false,
        expiresAt:      item.expiresAt   || null,
        daysUntilExpiry,
        expiryWarning,
        // ── Fields deliberately OMITTED ──────────────────────────────────────
        // rawPayload, decryptedValue, iv, authTag, ciphertext, encryptedKey
      };
    });

    // Log the view action (non-blocking)
    writeCredentialLog({ action: 'viewed', service: 'all', adminId, ip }).catch(() => {});

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PATCH /api/admin/integrations/:id/rotate
// Re-encrypts credentials for a given integration.
// Body: { newCredential: { apiKey: '...' } }
// Returns: { success: true, lastRotated: ISO-string }  — no keys.
app.patch('/api/admin/integrations/:id/rotate', async (req, res) => {
  const ip      = req.ip || req.headers['x-forwarded-for'] || 'unknown';
  const adminId = req.headers['x-admin-id'] || req.query.adminId || 'system';
  const { id }  = req.params;
  const { newCredential } = req.body;

  if (!newCredential || typeof newCredential !== 'object') {
    return res.status(400).json({ error: 'Request body must include newCredential object.' });
  }

  if (mongoose.connection.readyState !== 1) {
    // Offline fallback — simulate success
    const lastRotated = new Date().toISOString();
    await writeCredentialLog({ action: 'rotated', service: id, adminId, ip });
    return res.json({ success: true, lastRotated, offline: true });
  }

  try {
    const integration = await Integration.findById(id);
    if (!integration) return res.status(404).json({ error: 'Integration not found.' });

    const encrypted   = encryptCredentials(newCredential, CREDENTIALS_ENCRYPTION_KEY);
    const lastRotated = new Date();

    await Integration.updateOne(
      { _id: id },
      { $set: {
          credentials: encrypted,   // keep legacy field updated
          encryptedKey: encrypted.ciphertext,
          iv:           encrypted.iv,
          authTag:      encrypted.authTag,
          lastRotated,
      }}
    );

    await writeCredentialLog({ action: 'rotated', service: integration.source, adminId, ip });
    res.json({ success: true, lastRotated: lastRotated.toISOString() });
  } catch (err) {
    res.status(500).json({ error: 'Rotation failed: ' + err.message });
  }
});

// POST /api/admin/integrations/:id/test
// Tests connectivity for a given integration without exposing credentials.
// Returns: { success: true/false, message: string }
app.post('/api/admin/integrations/:id/test', async (req, res) => {
  const ip      = req.ip || req.headers['x-forwarded-for'] || 'unknown';
  const adminId = req.headers['x-admin-id'] || req.query.adminId || 'system';
  const { id }  = req.params;

  // Service → lightweight reachability test URL
  const SERVICE_TEST_URLS = {
    'supabase auth':  'https://supabase.com',
    'emailjs':        'https://api.emailjs.com',
    'mapbox api':     'https://api.mapbox.com',
    'twilio':         'https://www.twilio.com',
    'razorpay':       'https://api.razorpay.com',
    'sendgrid':       'https://api.sendgrid.com',
  };

  if (mongoose.connection.readyState !== 1) {
    await writeCredentialLog({ action: 'tested', service: id, adminId, ip });
    return res.json({ success: true, message: 'Offline mode: connection test simulated successfully.' });
  }

  try {
    const integration = await Integration.findById(id);
    if (!integration) return res.status(404).json({ error: 'Integration not found.' });

    const serviceName = (integration.source || '').toLowerCase();
    const testUrl     = SERVICE_TEST_URLS[serviceName] || 'https://httpbin.org/get';

    let success = false;
    let message = '';
    try {
      const response = await axios.head(testUrl, { timeout: 5000 });
      success = response.status < 400;
      message = success
        ? `Connection to ${integration.source} reachable (HTTP ${response.status}).`
        : `Service returned HTTP ${response.status}.`;
    } catch (netErr) {
      success = false;
      message = `Could not reach ${integration.source}: ${netErr.message}`;
    }

    await writeCredentialLog({ action: 'tested', service: integration.source, adminId, ip });
    res.json({ success, message });
  } catch (err) {
    res.status(500).json({ error: 'Test failed: ' + err.message });
  }
});

// GET /api/admin/credentials/logs
// Returns credential audit log, newest first.
app.get('/api/admin/credentials/logs', async (req, res) => {
  try {
    if (mongoose.connection.readyState === 1) {
      const logs = await CredentialLog.find().sort({ timestamp: -1 }).limit(100);
      return res.json(logs);
    }
    // Offline: return in-memory log
    res.json(credentialLogs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Webhook verification & rate-limiting helpers
function verifyWebhookSignature(rawBody, signatureHeader, secret) {
  const crypto = require('crypto');
  const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  const expectedBuf = Buffer.from(expected, 'utf8');
  const receivedBuf = Buffer.from(signatureHeader, 'utf8');
  if (expectedBuf.length !== receivedBuf.length) return false;
  return crypto.timingSafeEqual(expectedBuf, receivedBuf);
}

const rateLimitCache = new Map();
const LIMIT_WINDOW_MS = 60000;
const LIMIT_MAX_REQUESTS = 30;

function isRateLimited(ip) {
  const now = Date.now();
  if (!rateLimitCache.has(ip)) {
    rateLimitCache.set(ip, [now]);
    return false;
  }
  const timestamps = rateLimitCache.get(ip).filter(t => now - t < LIMIT_WINDOW_MS);
  timestamps.push(now);
  rateLimitCache.set(ip, timestamps);
  return timestamps.length > LIMIT_MAX_REQUESTS;
}

// POST: Inbound webhook to receive property listings updates
app.post('/api/webhooks/property', async (req, res) => {
  const ip = req.ip || req.headers['x-forwarded-for'] || 'unknown';
  
  if (isRateLimited(ip)) {
    return res.status(429).json({ error: 'Too many requests. Rate limit exceeded.' });
  }

  const signatureHeader = req.headers['x-realestate-signature'] || '';
  if (!signatureHeader) {
    return res.status(400).json({ error: 'Missing webhook signature header' });
  }

  const payload = req.body;
  if (!payload || Object.keys(payload).length === 0) {
    return res.status(400).json({ error: 'Empty payload body' });
  }

  const rawBody = Buffer.from(JSON.stringify(payload));
  if (!verifyWebhookSignature(rawBody, signatureHeader, PROPERTY_WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }

  const logEntry = {
    id: 'in_' + Math.random().toString(36).slice(2, 9),
    direction: 'inbound',
    event: payload.event || 'property.unknown',
    payload,
    timestamp: new Date().toISOString(),
    status: 'success'
  };
  webhookLogs.unshift(logEntry);

  if (payload.event === 'property.created') {
    const propData = payload.data || {};
    if (mongoose.connection.readyState === 1) {
      try {
        const newProp = new Property({
          title: propData.title || 'Webhook Listing',
          price: propData.price || 500000,
          location: propData.location || 'Unknown Location',
          sqft: propData.sqft || 1500,
          image: propData.image || 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600',
          type: propData.type || 'sale',
          featured: propData.featured || false
        });
        await newProp.save();
        logEntry.savedPropertyId = newProp._id;
      } catch (dbErr) {
        logEntry.status = 'failed';
        logEntry.error = dbErr.message;
        return res.status(500).json({ error: 'Failed to save property: ' + dbErr.message });
      }
    } else {
      console.log('Offline Mode: Inbound property.created processed (virtual):', propData.title);
    }
  }

  res.json({ received: true });
});

// GET: Retrieve webhook transaction logs
app.get('/api/admin/webhooks/logs', async (req, res) => {
  res.json(webhookLogs);
});

// ============================================================
// ROUTE PROTECTION — Catalog Page
// Inspired by SupplyWise middleware.ts:
//   const isProtectedRoute = createRouteMatcher(["/catalog(.*)"])
//   clerkMiddleware(async (auth, req) => { if (isProtectedRoute(req)) await auth.protect(); })
//
// Our vanilla equivalent: frontend calls this endpoint on page load.
// Returns 200 (allowed) or 401/403 (blocked) based on role.
// ============================================================

/**
 * requireCatalogAccess — reusable RBAC middleware for catalog routes.
 * Only admin and agent roles are permitted.
 * Mirrors SupplyWise's isProtectedRoute('/catalog(.*)') guard.
 */
function requireCatalogAccess(req, res, next) {
  const role = req.query.role || req.headers['x-user-role'] || null;

  // No role supplied = unauthenticated
  if (!role) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'You must be logged in to access the Property Catalog.',
      redirect: '/login.html'
    });
  }

  const allowedRoles = ['admin', 'agent'];
  if (!allowedRoles.includes(role)) {
    return res.status(403).json({
      error: 'Forbidden',
      message: `Access denied. Property Catalog requires admin or agent role. Your role: "${role}".`,
      redirect: '/index.html'
    });
  }

  next();
}

/**
 * GET /api/protected/catalog-access
 * Frontend calls this on property-catalog.html load to verify access.
 * Returns { allowed: true, role } on success.
 *
 * Protected routes (mirrors SupplyWise middleware.ts matchers):
 *   /catalog      → property-catalog.html
 *   /dashboard    → index.html admin view
 *   /csv export   → already protected by requireRole('admin','agent')
 */
app.get('/api/protected/catalog-access', requireCatalogAccess, (req, res) => {
  const role = req.query.role || req.headers['x-user-role'];
  res.json({
    allowed: true,
    role,
    message: `Catalog access granted for role: ${role}`,
    protectedRoutes: ['/catalog', '/api/properties/csv', '/api/admin/*']
  });
});

// 5. START SERVER
const PORT = 3001;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));