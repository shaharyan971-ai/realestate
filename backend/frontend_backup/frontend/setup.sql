-- ================================================================
-- RealEstate App — Supabase Database Setup
-- Run this ENTIRE script in:
--   https://supabase.com/dashboard/project/ynsefltcqtffcdmxwpbn/sql/new
-- ================================================================

-- 1. PROFILES TABLE
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY,
  full_name TEXT,
  role TEXT DEFAULT 'buyer',
  phone TEXT,
  city TEXT,
  address TEXT,
  photo_url TEXT,
  avatar_url TEXT,
  bio TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1a. ADD MISSING COLUMNS (for existing deployments — safe to re-run)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- 2. PROPERTIES TABLE
CREATE TABLE IF NOT EXISTS properties (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner_id UUID,
  title TEXT NOT NULL,
  listing_type TEXT DEFAULT 'Sale',
  category TEXT DEFAULT 'Apartment',
  city TEXT,
  locality TEXT,
  location TEXT,
  address TEXT,
  price NUMERIC,
  bedrooms INTEGER DEFAULT 0,
  bathrooms INTEGER DEFAULT 0,
  area NUMERIC,
  deal_score TEXT DEFAULT 'Fair Price',
  image TEXT,
  contact_name TEXT,
  contact_phone TEXT,
  is_verified BOOLEAN DEFAULT false,
  total_views INTEGER DEFAULT 0,
  amenities JSONB DEFAULT '[]',
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2a. ADD MISSING COLUMNS (for existing deployments — safe to re-run)
ALTER TABLE properties ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS locality TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS address TEXT;

-- 3. FAVORITES TABLE
CREATE TABLE IF NOT EXISTS favorites (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, property_id)
);

-- 4. MESSAGES TABLE
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  sender_id UUID NOT NULL,
  receiver_id UUID NOT NULL,
  property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
  text TEXT NOT NULL,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. ENABLE ROW LEVEL SECURITY
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 6. RLS POLICIES — allow public read + any insert (demo mode)
DROP POLICY IF EXISTS "Public read properties" ON properties;
CREATE POLICY "Public read properties" ON properties FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone insert properties" ON properties;
CREATE POLICY "Anyone insert properties" ON properties FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone update properties" ON properties;
CREATE POLICY "Anyone update properties" ON properties FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Anyone delete properties" ON properties;
CREATE POLICY "Anyone delete properties" ON properties FOR DELETE USING (true);

DROP POLICY IF EXISTS "Public read profiles" ON profiles;
CREATE POLICY "Public read profiles" ON profiles FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone insert profiles" ON profiles;
CREATE POLICY "Anyone insert profiles" ON profiles FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Anyone update profiles" ON profiles;
CREATE POLICY "Anyone update profiles" ON profiles FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Favorites all" ON favorites;
CREATE POLICY "Favorites all" ON favorites FOR ALL USING (true);

DROP POLICY IF EXISTS "Messages select" ON messages;
CREATE POLICY "Messages select" ON messages FOR SELECT USING (true);

DROP POLICY IF EXISTS "Messages insert" ON messages;
CREATE POLICY "Messages insert" ON messages FOR INSERT WITH CHECK (true);


-- 7. INSERT 14 SAMPLE PROPERTIES
INSERT INTO properties (title, listing_type, category, location, price, bedrooms, bathrooms, area, deal_score, image, contact_name, contact_phone, is_verified, total_views, amenities)
VALUES
  ('3 BHK Sea View Apartment',       'Sale', 'Apartment', 'Bandra West, Mumbai',        12500000, 3, 2, 1450,  'Fair Price',  'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=700', 'Rohan Mehta',    '9876543210', true,  428,  '["Parking","Gym","Lift","Security","Sea View"]'),
  ('Cozy 2 BHK Apartment',           'Rent', 'Apartment', 'Koregaon Park, Pune',         35000,    2, 2, 1100,  'Great Deal',  'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=700', 'Pooja Desai',    '9123456789', true,  312,  '["Parking","Gym","Lift","Furnished"]'),
  ('Modern Studio Apartment',        'Rent', 'Apartment', 'Connaught Place, Delhi',      28000,    1, 1, 620,   'Fair Price',  'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=700', 'Arjun Kapoor',   '9988776655', false, 195,  '["Lift","Security","Furnished"]'),
  ('Budget 2 BHK Society Flat',      'Sale', 'Apartment', 'Salt Lake, Kolkata',          4800000,  2, 2, 1050,  'Great Deal',  'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=700', 'Subhasis Ghosh', '9001234567', true,  276,  '["Lift","Parking","Security"]'),
  ('Penthouse with Private Terrace', 'Sale', 'Apartment', 'Worli, Mumbai',               45000000, 4, 4, 5200,  'Overpriced',  'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=700', 'Nikhil Shah',    '9871234560', true,  891,  '["Parking","Pool","Gym","Lift","Furnished","Security","Garden"]'),
  ('Premium 2 BHK Near Metro',       'Rent', 'Apartment', 'Sector 62, Noida',            22000,    2, 2, 980,   'Fair Price',  'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=700', 'Kavita Sharma',  '9811223344', false, 143,  '["Parking","Lift","Power Backup"]'),
  ('Fully Furnished 3 BHK',          'Rent', 'Apartment', 'DLF Phase 2, Gurgaon',       55000,    3, 3, 1800,  'Fair Price',  'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=700', 'Rahul Gupta',    '9654321098', true,  522,  '["Parking","Gym","Pool","Lift","Furnished","Security"]'),
  ('Luxurious 4 BHK Garden Villa',   'Sale', 'Villa',     'Whitefield, Bangalore',       18000000, 4, 4, 3200,  'Great Deal',  'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=700', 'Suresh Nair',    '9845678901', true,  674,  '["Parking","Pool","Garden","Security","Power Backup"]'),
  ('Elegant 5 BHK Seafront Villa',   'Sale', 'Villa',     'Adyar, Chennai',              25000000, 5, 5, 4500,  'Fair Price',  'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=700', 'Meena Iyer',     '9934567890', true,  389,  '["Parking","Pool","Gym","Garden","Security","Power Backup"]'),
  ('Spacious 3 BHK Independent House','Sale','House',     'Jubilee Hills, Hyderabad',    9500000,  3, 3, 2200,  'Great Deal',  'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=700', 'Prakash Reddy',  '9700112233', true,  461,  '["Parking","Garden","Security"]'),
  ('4 BHK Colonial Bungalow',        'Rent', 'House',     'Boat Club Road, Pune',        90000,    4, 3, 3000,  'Overpriced',  'https://images.unsplash.com/photo-1598228723793-52759bba239c?w=700', 'Aditya Joshi',   '9099887766', false, 208,  '["Parking","Garden","Power Backup"]'),
  ('Prime Residential Plot – Corner','Sale', 'Plot',      'Sarjapur Road, Bangalore',    7500000,  0, 0, 2400,  'Great Deal',  'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=700', 'Vijay Kumar',    '9561230987', true,  317,  '["Corner Plot","Road Facing","BMRDA Approved"]'),
  ('Commercial Office Space',        'Rent', 'Commercial','MG Road, Bangalore',          120000,   0, 2, 2400,  'Fair Price',  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=700', 'Divya Menon',    '9812345670', true,  543,  '["Parking","Lift","Power Backup","Security"]'),
  ('Retail Showroom on High Street', 'Sale', 'Commercial','Linking Road, Mumbai',        32000000, 0, 1, 1800,  'Overpriced',  'https://images.unsplash.com/photo-1421941027568-40ab08ee5592?w=700', 'Farhan Sheikh',  '9723456789', true,  712,  '["Parking","AC","High Footfall","CCTV"]');

-- Done!
SELECT COUNT(*) AS total_properties FROM properties;
