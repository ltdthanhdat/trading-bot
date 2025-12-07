# Bot Trade

Crypto Trading Bot sử dụng thư viện Freqtrade.

## Quick Start

```bash
# 1. Setup
uv sync

# 2. Tạo config
cp config/config.json.example config/config.json

# 3. Chạy bot
uv run freqtrade trade --config config/config.json --strategy MyStrategy
```

## Cấu trúc Project

```
bot-trade/
├── config/              # Configuration files
├── src/
│   └── bot_trade/
│       └── strategies/  # Trading strategies
├── user_data/           # Runtime data (logs, results, market data)
└── tests/               # Tests
```

## Requirements

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) package manager

## Documentation

Xem [CLAUDE.md](CLAUDE.md) để biết cách sử dụng chi tiết.

## License

MIT
