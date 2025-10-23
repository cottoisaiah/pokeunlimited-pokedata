-- ========================================
-- TCGdex Extended Card Fields Migration
-- ========================================
-- Adds columns for abilities, attacks, weaknesses, resistances, and variants
-- Run this for ALL language tables

-- Function to add columns to a specific language table
CREATE OR REPLACE FUNCTION add_extended_card_fields(lang_code TEXT) RETURNS void AS $$
DECLARE
    table_name TEXT := 'pokedata_cards_' || lang_code;
BEGIN
    -- Add abilities column (array of ability objects)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS abilities JSONB DEFAULT NULL
    ', table_name);
    
    -- Add attacks column (array of attack objects)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS attacks JSONB DEFAULT NULL
    ', table_name);
    
    -- Add weaknesses column (array of weakness objects)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS weaknesses JSONB DEFAULT NULL
    ', table_name);
    
    -- Add resistances column (array of resistance objects)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS resistances JSONB DEFAULT NULL
    ', table_name);
    
    -- Add variants column (object with variant information)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS variants JSONB DEFAULT NULL
    ', table_name);
    
    -- Add suffix column (V, VMAX, GX, etc.)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS suffix VARCHAR(20) DEFAULT NULL
    ', table_name);
    
    -- Add dex_id column (Pokedex numbers array)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS dex_id INTEGER[] DEFAULT NULL
    ', table_name);
    
    -- Add regulation_mark column (tournament legality)
    EXECUTE format('
        ALTER TABLE %I 
        ADD COLUMN IF NOT EXISTS regulation_mark VARCHAR(5) DEFAULT NULL
    ', table_name);
    
    RAISE NOTICE 'Extended fields added to table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- Apply to all language tables
DO $$
DECLARE
    lang TEXT;
    langs TEXT[] := ARRAY['en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id'];
BEGIN
    FOREACH lang IN ARRAY langs
    LOOP
        PERFORM add_extended_card_fields(lang);
    END LOOP;
    
    RAISE NOTICE 'Migration complete! Extended fields added to all language tables.';
END;
$$;

-- Create indexes for better query performance
DO $$
DECLARE
    lang TEXT;
    langs TEXT[] := ARRAY['en', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'nl', 'pl', 'pt_br', 'ru', 'th', 'zh_cn', 'zh_tw', 'id'];
    table_name TEXT;
BEGIN
    FOREACH lang IN ARRAY langs
    LOOP
        table_name := 'pokedata_cards_' || lang;
        
        -- Index on suffix for filtering V, VMAX, etc.
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS %I ON %I (suffix)
        ', table_name || '_suffix_idx', table_name);
        
        -- Index on regulation_mark for tournament queries
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS %I ON %I (regulation_mark)
        ', table_name || '_regulation_idx', table_name);
        
        -- GIN index on abilities for JSON queries
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (abilities)
        ', table_name || '_abilities_idx', table_name);
        
        -- GIN index on attacks for JSON queries
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (attacks)
        ', table_name || '_attacks_idx', table_name);
        
    END LOOP;
    
    RAISE NOTICE 'Indexes created successfully!';
END;
$$;

-- Verify migration
SELECT 
    table_name,
    COUNT(*) FILTER (WHERE column_name = 'abilities') as has_abilities,
    COUNT(*) FILTER (WHERE column_name = 'attacks') as has_attacks,
    COUNT(*) FILTER (WHERE column_name = 'weaknesses') as has_weaknesses,
    COUNT(*) FILTER (WHERE column_name = 'resistances') as has_resistances,
    COUNT(*) FILTER (WHERE column_name = 'variants') as has_variants,
    COUNT(*) FILTER (WHERE column_name = 'suffix') as has_suffix,
    COUNT(*) FILTER (WHERE column_name = 'dex_id') as has_dex_id,
    COUNT(*) FILTER (WHERE column_name = 'regulation_mark') as has_regulation_mark
FROM information_schema.columns
WHERE table_name LIKE 'pokedata_cards_%'
    AND column_name IN ('abilities', 'attacks', 'weaknesses', 'resistances', 'variants', 'suffix', 'dex_id', 'regulation_mark')
GROUP BY table_name
ORDER BY table_name;
