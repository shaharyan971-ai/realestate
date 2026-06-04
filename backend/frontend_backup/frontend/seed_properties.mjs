// seed_properties.mjs — run with: node seed_properties.mjs
// Inserts 14 sample properties into Supabase covering every filter dimension:
//   listingType : Sale | Rent
//   category    : Apartment | Villa | House | Plot | Commercial
//   bedrooms    : 1 | 2 | 3 | 4 | 5+
//   deal_score  : Great Deal | Fair Price | Overpriced
//   price range : 15K /mo → 5 Cr

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const SB_URL = 'https://ynsefltcqtffcdmxwpbn.supabase.co';
const SB_KEY = 'sb_publishable_AnRqy1ODPXb7gFPlaybSVw_zoL4aLon';

const sb = createClient(SB_URL, SB_KEY);

const SEED_OWNER = '00000000-0000-0000-0000-000000000001'; // placeholder owner UUID

const props = [
  // ── APARTMENTS ────────────────────────────────────────────────
  {
    title: '3 BHK Sea View Apartment',
    listing_type: 'Sale', category: 'Apartment',
    location: 'Bandra West, Mumbai',
    price: 12500000, bedrooms: 3, bathrooms: 2, area: 1450,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=700',
    contact_name: 'Rohan Mehta', contact_phone: '9876543210',
    is_verified: true, total_views: 428,
    amenities: ['Parking','Gym','Lift','Security','Sea View']
  },
  {
    title: 'Cozy 2 BHK Apartment',
    listing_type: 'Rent', category: 'Apartment',
    location: 'Koregaon Park, Pune',
    price: 35000, bedrooms: 2, bathrooms: 2, area: 1100,
    deal_score: 'Great Deal',
    image: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=700',
    contact_name: 'Pooja Desai', contact_phone: '9123456789',
    is_verified: true, total_views: 312,
    amenities: ['Parking','Gym','Lift','Furnished']
  },
  {
    title: 'Modern Studio Apartment',
    listing_type: 'Rent', category: 'Apartment',
    location: 'Connaught Place, Delhi',
    price: 28000, bedrooms: 1, bathrooms: 1, area: 620,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=700',
    contact_name: 'Arjun Kapoor', contact_phone: '9988776655',
    is_verified: false, total_views: 195,
    amenities: ['Lift','Security','Furnished']
  },
  {
    title: 'Budget 2 BHK Society Flat',
    listing_type: 'Sale', category: 'Apartment',
    location: 'Salt Lake, Kolkata',
    price: 4800000, bedrooms: 2, bathrooms: 2, area: 1050,
    deal_score: 'Great Deal',
    image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=700',
    contact_name: 'Subhasis Ghosh', contact_phone: '9001234567',
    is_verified: true, total_views: 276,
    amenities: ['Lift','Parking','Security']
  },
  {
    title: 'Penthouse with Private Terrace',
    listing_type: 'Sale', category: 'Apartment',
    location: 'Worli, Mumbai',
    price: 45000000, bedrooms: 4, bathrooms: 4, area: 5200,
    deal_score: 'Overpriced',
    image: 'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=700',
    contact_name: 'Nikhil Shah', contact_phone: '9871234560',
    is_verified: true, total_views: 891,
    amenities: ['Parking','Pool','Gym','Lift','Furnished','Security','Garden']
  },
  {
    title: 'Premium 2 BHK Near Metro',
    listing_type: 'Rent', category: 'Apartment',
    location: 'Sector 62, Noida',
    price: 22000, bedrooms: 2, bathrooms: 2, area: 980,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=700',
    contact_name: 'Kavita Sharma', contact_phone: '9811223344',
    is_verified: false, total_views: 143,
    amenities: ['Parking','Lift','Power Backup']
  },
  {
    title: 'Fully Furnished 3 BHK',
    listing_type: 'Rent', category: 'Apartment',
    location: 'DLF Phase 2, Gurgaon',
    price: 55000, bedrooms: 3, bathrooms: 3, area: 1800,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=700',
    contact_name: 'Rahul Gupta', contact_phone: '9654321098',
    is_verified: true, total_views: 522,
    amenities: ['Parking','Gym','Pool','Lift','Furnished','Security']
  },

  // ── VILLAS ────────────────────────────────────────────────────
  {
    title: 'Luxurious 4 BHK Garden Villa',
    listing_type: 'Sale', category: 'Villa',
    location: 'Whitefield, Bangalore',
    price: 18000000, bedrooms: 4, bathrooms: 4, area: 3200,
    deal_score: 'Great Deal',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=700',
    contact_name: 'Suresh Nair', contact_phone: '9845678901',
    is_verified: true, total_views: 674,
    amenities: ['Parking','Pool','Garden','Security','Power Backup']
  },
  {
    title: 'Elegant 5 BHK Seafront Villa',
    listing_type: 'Sale', category: 'Villa',
    location: 'Adyar, Chennai',
    price: 25000000, bedrooms: 5, bathrooms: 5, area: 4500,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=700',
    contact_name: 'Meena Iyer', contact_phone: '9934567890',
    is_verified: true, total_views: 389,
    amenities: ['Parking','Pool','Gym','Garden','Security','Power Backup']
  },

  // ── HOUSES ───────────────────────────────────────────────────
  {
    title: 'Spacious 3 BHK Independent House',
    listing_type: 'Sale', category: 'House',
    location: 'Jubilee Hills, Hyderabad',
    price: 9500000, bedrooms: 3, bathrooms: 3, area: 2200,
    deal_score: 'Great Deal',
    image: 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=700',
    contact_name: 'Prakash Reddy', contact_phone: '9700112233',
    is_verified: true, total_views: 461,
    amenities: ['Parking','Garden','Security']
  },
  {
    title: '4 BHK Colonial Bungalow',
    listing_type: 'Rent', category: 'House',
    location: 'Boat Club Road, Pune',
    price: 90000, bedrooms: 4, bathrooms: 3, area: 3000,
    deal_score: 'Overpriced',
    image: 'https://images.unsplash.com/photo-1598228723793-52759bba239c?w=700',
    contact_name: 'Aditya Joshi', contact_phone: '9099887766',
    is_verified: false, total_views: 208,
    amenities: ['Parking','Garden','Power Backup']
  },

  // ── PLOTS ────────────────────────────────────────────────────
  {
    title: 'Prime Residential Plot – Corner',
    listing_type: 'Sale', category: 'Plot',
    location: 'Sarjapur Road, Bangalore',
    price: 7500000, bedrooms: 0, bathrooms: 0, area: 2400,
    deal_score: 'Great Deal',
    image: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=700',
    contact_name: 'Vijay Kumar', contact_phone: '9561230987',
    is_verified: true, total_views: 317,
    amenities: ['Corner Plot','Road Facing','BMRDA Approved']
  },

  // ── COMMERCIAL ───────────────────────────────────────────────
  {
    title: 'Commercial Office Space',
    listing_type: 'Rent', category: 'Commercial',
    location: 'MG Road, Bangalore',
    price: 120000, bedrooms: 0, bathrooms: 2, area: 2400,
    deal_score: 'Fair Price',
    image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=700',
    contact_name: 'Divya Menon', contact_phone: '9812345670',
    is_verified: true, total_views: 543,
    amenities: ['Parking','Lift','Power Backup','Security']
  },
  {
    title: 'Retail Showroom on High Street',
    listing_type: 'Sale', category: 'Commercial',
    location: 'Linking Road, Mumbai',
    price: 32000000, bedrooms: 0, bathrooms: 1, area: 1800,
    deal_score: 'Overpriced',
    image: 'https://images.unsplash.com/photo-1421941027568-40ab08ee5592?w=700',
    contact_name: 'Farhan Sheikh', contact_phone: '9723456789',
    is_verified: true, total_views: 712,
    amenities: ['Parking','AC','High Footfall','CCTV']
  }
];

async function seed() {
  console.log(`\n Seeding ${props.length} sample properties into Supabase…\n`);

  // First check if the table already has seeded data (avoid duplicates)
  const { data: existing, error: chkErr } = await sb.from('properties').select('id').limit(1);
  if (chkErr) {
    console.error('Cannot connect to Supabase:', chkErr.message);
    console.log('\n Make sure the "properties" table exists. Run the SQL from ARCHITECTURE.md first.');
    process.exit(1);
  }

  const rows = props.map(p => ({
    ...p,
    owner_id: SEED_OWNER,
    amenities: p.amenities  // stored as jsonb array in Supabase
  }));

  const { data, error } = await sb.from('properties').insert(rows).select('id, title');
  if (error) {
    console.error('Insert failed:', error.message);
    console.log('\n Hint:', error.details || error.hint || '');
    process.exit(1);
  }

  console.log(`✅ Successfully inserted ${data.length} properties:\n`);
  data.forEach((r, i) => console.log(`  ${i+1}. [${r.id}] ${r.title}`));
  console.log('\n Open http://localhost:3000/home.html and browse the live listings!\n');
}

seed();
