# Claude Guide

Hướng dẫn chi tiết cho AI Agent khi làm việc với project này.

## Cấu trúc Project

```
bot-trade/
├── config/              # Configuration files
│   ├── config.json      # Main config (gitignored)
│   └── config.json.example
├── src/
│   └── bot_trade/
│       ├── strategies/  # Trading strategies
│       └── utils/       # Utilities
├── user_data/           # Runtime data only
│   ├── data/            # Market data (feather format)
│   ├── backtest_results/
│   ├── plot/
│   └── logs/
└── tests/
```

## Quy tắc quan trọng

### 1. Config
- Config files ở `config/`
- `config.json` được gitignore (chứa secrets)
- Luôn dùng `config/config.json` khi chạy lệnh

### 2. Strategies
- Tất cả strategies ở `src/bot_trade/strategies/`
- Strategy path: `src/bot_trade/strategies`
- Config đã set `strategy_path` tự động

### 3. Data
- Market data ở `user_data/data/<exchange>/`
- Format mặc định: `feather`
- File pattern: `<PAIR>-<TIMEFRAME>.feather`

### 4. Dependencies
- Sử dụng `uv` để quản lý dependencies
- Freqtrade được cài từ git: `git+ssh://git@github.com/freqtrade/freqtrade.git@develop`
- Chạy lệnh: `uv run freqtrade <command>`

## Cài đặt

### Yêu cầu

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) - Package manager

Cài đặt uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup project

```bash
# Sync dependencies (tự động tạo .venv)
uv sync
```

Freqtrade sẽ được cài tự động từ git repository.

### Quản lý dependencies

```bash
# Thêm package
uv add <package-name>

# Thêm dev dependency
uv add --dev <package-name>

# Xóa package
uv remove <package-name>

# Sync từ pyproject.toml
uv sync
```

## Cấu hình

### Tạo config

```bash
# Copy từ example
cp config/config.json.example config/config.json

# Hoặc tạo mới
uv run freqtrade new-config --config config/config.json
```

### Chỉnh sửa config

Mở `config/config.json` và chỉnh sửa:
- **Exchange**: Chọn sàn (binance, kraken, v.v.)
- **API Keys**: Thêm key và secret (nếu giao dịch thật)
- **dry_run**: Đặt `true` để test không dùng tiền thật
- **pair_whitelist**: Danh sách cặp coin

## Cách chạy

### Download dữ liệu

**Quan trọng**: Cần download data trước khi backtest!

```bash
# Download cơ bản (30 ngày)
uv run freqtrade download-data \
    --exchange binance \
    --pairs BTC/USDT ETH/USDT \
    --timeframes 5m 1h \
    --days 60 \
    --config config/config.json

# Download với timerange cụ thể
uv run freqtrade download-data \
    --exchange binance \
    --pairs BTC/USDT \
    --timerange 20240101- \
    --config config/config.json

# Xem dữ liệu đã download
uv run freqtrade list-data --config config/config.json
```

**Vị trí lưu trữ:**
- `user_data/data/<exchange>/<PAIR>-<TIMEFRAME>.feather`
- Format mặc định: `feather` (Apache Arrow, nhanh nhất)

### Backtesting

```bash
# Backtest với timerange
uv run freqtrade backtesting \
    --config config/config.json \
    --strategy MyStrategy \
    --timerange 20240101-20241201

# Backtest với dữ liệu hiện có
uv run freqtrade backtesting \
    --config config/config.json \
    --strategy MyStrategy
```

### Chạy bot

```bash
# Chạy bot (dry-run)
uv run freqtrade trade \
    --config config/config.json \
    --strategy MyStrategy

# Hoặc activate environment
source .venv/bin/activate
freqtrade trade --config config/config.json --strategy MyStrategy
```

### Tạo strategy mới

```bash
# Tạo từ template
uv run freqtrade new-strategy \
    --strategy MyNewStrategy \
    --strategy-path src/bot_trade/strategies

# Strategy sẽ được tạo tại: src/bot_trade/strategies/MyNewStrategy.py
```

### Các lệnh khác

```bash
# List strategies
uv run freqtrade list-strategies --strategy-path src/bot_trade/strategies

# List exchanges
uv run freqtrade list-exchanges

# Hyperopt (tối ưu tham số)
uv run freqtrade hyperopt \
    --config config/config.json \
    --strategy MyStrategy \
    --hyperopt-loss SharpeHyperOptLoss \
    --epochs 100

# Plot kết quả
uv run freqtrade plot-profit --config config/config.json --strategy MyStrategy
uv run freqtrade plot-dataframe \
    --config config/config.json \
    --strategy MyStrategy \
    --pairs BTC/USDT \
    --indicators1 rsi \
    --indicators2 macd macdsignal
```

## Strategy Development

### Tạo Strategy mới

1. Tạo file trong `src/bot_trade/strategies/`:

```python
from freqtrade.strategy import IStrategy
import talib.abstract as ta

class MyStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    stoploss = -0.10
    minimal_roi = {"0": 0.04}
    
    def populate_indicators(self, dataframe, metadata):
        dataframe["rsi"] = ta.RSI(dataframe)
        return dataframe
    
    def populate_entry_trend(self, dataframe, metadata):
        dataframe.loc[
            (dataframe["rsi"] < 30),
            "enter_long",
        ] = 1
        return dataframe
    
    def populate_exit_trend(self, dataframe, metadata):
        dataframe.loc[
            (dataframe["rsi"] > 70),
            "exit_long",
        ] = 1
        return dataframe
```

2. Chạy bot:

```bash
uv run freqtrade trade --config config/config.json --strategy MyStrategy
```

## File paths quan trọng

- Config: `config/config.json`
- Strategy path: `src/bot_trade/strategies`
- Data dir: `user_data/data`
- User data dir: `user_data`

## Lưu ý khi code

1. **Luôn dùng paths tương đối từ root**: `config/config.json`, không phải `./config/config.json`
2. **Strategy path**: Đã được set trong config, không cần chỉ định lại
3. **Data format**: Mặc định là `feather`, không cần chỉ định
4. **Dry run**: Luôn test với `dry_run: true` trước

## Testing

Khi test, đảm bảo:
- Config file tồn tại: `config/config.json`
- Strategy tồn tại: `src/bot_trade/strategies/MyStrategy.py`
- Data đã download (nếu backtest): `user_data/data/<exchange>/`

## Lưu ý quan trọng

⚠️ **CẢNH BÁO**: 
- Luôn bắt đầu với `dry_run: true` để test không dùng tiền thật
- Backtest strategy trước khi giao dịch thật
- Giao dịch có rủi ro, không đảm bảo lợi nhuận

## Tài liệu tham khảo

- [Freqtrade Documentation](https://www.freqtrade.io)
- [Strategy Customization](https://www.freqtrade.io/en/latest/strategy-customization/)
- [Strategy 101](https://www.freqtrade.io/en/latest/strategy-101/)
- [Backtesting Guide](https://www.freqtrade.io/en/latest/backtesting/)
