# 🎯 PokeData Import System

A comprehensive Pokemon TCG data pipeline that fetches card data from TCGdex and integrates real-time eBay pricing for multiple languages (English, Japanese, Chinese, Korean).

## 📋 Overview

This system provides:
- **Multi-language support**: EN, JA, ZH, KO
- **Complete card database**: All Pokemon TCG sets and cards
- **Real-time pricing**: eBay market data integration
- **Production-ready**: Async, scalable, and robust

## 🏗️ Architecture

```
TCGdex API ────► Import Service ────► PostgreSQL Database
     │                    │                    │
     └─ EN/JA/ZH/KO       └─ Data Processing    └─ pokedata_cards table
                          │                    │
eBay API ────────────────► └─ Pricing Updates   └─ eBay pricing columns
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- TCGdex API access
- eBay API credentials

### Installation

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Database setup:**
The system uses the existing `tradingcards` database. The `pokedata_cards` and `pokedata_sets` tables will be created automatically.

3. **Environment configuration:**
Set your database URL and API keys in environment variables or `.env` file:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tradingcards
EBAY_APP_ID=your_ebay_app_id
EBAY_CERT_ID=your_ebay_cert_id
```

### Usage

#### Import All Data
```bash
# Import all Pokemon TCG data for all languages
python manage_pokedata.py import

# Import only English data
python manage_pokedata.py import --language en

# Test with limited data (2 sets per language)
python manage_pokedata.py import --limit-sets 2
```

#### Update eBay Pricing
```bash
# Update pricing for all cards
python manage_pokedata.py pricing

# Update pricing for limited cards (testing)
python manage_pokedata.py pricing --limit 10
```

#### Check Database Status
```bash
python manage_pokedata.py status
```

## 📊 Database Schema

### pokedata_cards Table
```sql
CREATE TABLE pokedata_cards (
    id SERIAL PRIMARY KEY,
    tcgdex_id VARCHAR NOT NULL,
    local_id VARCHAR,
    name VARCHAR NOT NULL,
    language VARCHAR(2) NOT NULL,
    set_id VARCHAR NOT NULL,
    set_name VARCHAR,
    set_code VARCHAR,
    set_release_date DATE,
    set_total_cards INTEGER,
    category VARCHAR,
    rarity VARCHAR,
    illustrator VARCHAR,
    hp INTEGER,
    types TEXT[],
    stage VARCHAR,
    evolves_from VARCHAR,
    retreat_cost INTEGER,
    image_url VARCHAR,
    variants JSONB,
    legal JSONB,
    abilities JSONB,
    attacks JSONB,
    weaknesses JSONB,
    resistances JSONB,

    -- eBay Pricing Data
    ebay_avg_price DECIMAL(10,2),
    ebay_median_price DECIMAL(10,2),
    ebay_low_price DECIMAL(10,2),
    ebay_high_price DECIMAL(10,2),
    ebay_sold_count_30d INTEGER,
    ebay_active_listings INTEGER,
    market_price DECIMAL(10,2),
    last_ebay_update TIMESTAMP,
    is_priced BOOLEAN DEFAULT FALSE,

    -- Metadata
    raw_tcgdex_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tcgdex_id, language)
);
```

### pokedata_sets Table
```sql
CREATE TABLE pokedata_sets (
    id SERIAL PRIMARY KEY,
    tcgdex_id VARCHAR NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    code VARCHAR,
    language VARCHAR(2) NOT NULL,
    release_date DATE,
    total_cards INTEGER,
    logo_url VARCHAR,
    symbol_url VARCHAR,
    serie_name VARCHAR,
    serie_code VARCHAR,
    raw_tcgdex_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tcgdex_id, language)
);
```

## 🔧 API Reference

### PokeDataImportService

#### Import Methods
- `import_all_languages(limit_sets=None)` - Import all languages
- `import_language(language, limit_sets=None)` - Import specific language
- `update_ebay_pricing(limit=None)` - Update eBay pricing data

#### Supported Languages
- `'en'` - English
- `'ja'` - Japanese
- `'zh'` - Chinese (Simplified)
- `'ko'` - Korean

### TCGdex Data Fields

#### Card Data
- Basic info: `id`, `name`, `local_id`
- Set info: `set_id`, `set_name`, `set_code`
- Card attributes: `category`, `rarity`, `illustrator`
- Pokemon stats: `hp`, `types`, `stage`, `evolves_from`
- Game mechanics: `abilities`, `attacks`, `weaknesses`, `resistances`
- Variants: `normal`, `reverse`, `holo`, `firstEdition`
- Legal: `standard`, `expanded`

#### Set Data
- Basic info: `id`, `name`, `code`
- Metadata: `release_date`, `total_cards`
- Assets: `logo_url`, `symbol_url`
- Series: `serie_name`, `serie_code`

## 📈 Performance & Scaling

### Import Performance
- **Typical throughput**: 500-1000 cards/minute
- **Memory usage**: ~100MB for full import
- **Network requests**: Rate-limited to avoid API throttling

### Pricing Updates
- **Update frequency**: Recommended daily
- **eBay API limits**: 5000 calls/day for sandbox, higher for production
- **Pricing accuracy**: Based on recent sold listings

### Optimization Tips
1. **Batch processing**: Import sets sequentially, cards in batches
2. **Rate limiting**: Built-in delays between API calls
3. **Error handling**: Automatic retry with exponential backoff
4. **Database indexing**: Optimized for common query patterns

## 🧪 Testing

### SDK Test
```bash
python test_tcgdex_sdk.py
```

### Import Service Test
```bash
python test_pokedata_import.py
```

### Manual Testing
```bash
# Test English import (2 sets)
python manage_pokedata.py import --language en --limit-sets 2

# Check status
python manage_pokedata.py status

# Test pricing (5 cards)
python manage_pokedata.py pricing --limit 5
```

## 🔍 Monitoring & Troubleshooting

### Common Issues

#### Database Connection
```
ERROR: No module named 'psycopg2'
```
**Solution**: Install PostgreSQL adapter
```bash
pip install psycopg2-binary
```

#### TCGdex API Errors
```
ERROR: TCGdex API timeout
```
**Solution**: Check network connectivity, retry with smaller batches

#### eBay API Limits
```
ERROR: eBay API rate limit exceeded
```
**Solution**: Reduce update frequency, implement backoff strategy

### Logs & Debugging
- Enable debug logging: `python manage_pokedata.py --log-level DEBUG import`
- Check database status: `python manage_pokedata.py status`
- Monitor import progress in real-time

### Performance Monitoring
- Import statistics printed after each run
- Database status shows total counts by language
- Error counts help identify problematic data

## 🚢 Production Deployment

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ for full imports
- **Storage**: 10GB+ for complete card database
- **Network**: Stable internet for API calls

### Environment Setup
```bash
# Production environment
export ENVIRONMENT=production
export DATABASE_URL=postgresql+asyncpg://prod_user:prod_pass@prod_host:5432/tradingcards
export EBAY_APP_ID=your_production_app_id
export EBAY_CERT_ID=your_production_cert_id
```

### Automated Updates
Set up cron jobs for regular data updates:
```bash
# Daily full import (Sunday mornings)
0 2 * * 0 /path/to/manage_pokedata.py import

# Hourly pricing updates
0 * * * * /path/to/manage_pokedata.py pricing
```

### Backup Strategy
- **Database backups**: Daily PostgreSQL dumps
- **Configuration**: Version-controlled environment files
- **Logs**: Centralized logging with rotation

## 🤝 Contributing

### Code Standards
- Type hints for all functions
- Async/await for I/O operations
- Structured logging with `structlog`
- Comprehensive error handling

### Testing
- Unit tests for data processing logic
- Integration tests for API calls
- Performance tests for large imports

### Documentation
- Update this README for new features
- Document API changes
- Include performance benchmarks

## 📄 License

This project is part of the PokeUnlimited ecosystem. See main project license for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs with debug level enabled
3. Test with limited data first
4. Check TCGdex and eBay API status

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Languages Supported**: EN, JA, ZH, KO
**TCGdex SDK**: v2.2.0