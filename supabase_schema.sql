# Supabase Tables for GEO SaaS

## 1. brands table
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    city TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name)
);

## 2. audits table
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    confidence_score FLOAT,
    is_cited BOOLEAN,
    gaps_json JSONB,
    remediation_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

## 3. Enable RLS and Add Policies
-- Brands: Users can only see/edit their own brands
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own brands" ON brands FOR ALL USING (auth.uid() = user_id);

-- Audits: Users can only see audits for their own brands
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view audits for their brands" ON audits FOR SELECT USING (
    EXISTS (SELECT 1 FROM brands WHERE brands.id = audits.brand_id AND brands.user_id = auth.uid())
);
CREATE POLICY "Users can insert audits for their brands" ON audits FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM brands WHERE brands.id = audits.brand_id AND brands.user_id = auth.uid())
);
