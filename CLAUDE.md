# CLAUDE.md — Project Reference

## Project Instructions
- This is a Django project using **SQLite (`db.sqlite3`)** database
- Always check existing models before creating new ones — never duplicate
- Never overwrite existing logic, only extend it
- Always use existing naming conventions found in the codebase
- Check for duplicate functions/classes before adding new ones


### API & Backend Rules
- Follow Django REST Framework (DRF) patterns for all APIs
- Always add proper error handling (try/except, form validation, API errors)
- Add comments to complex logic
- Prefer class-based views (CBV) over function-based where possible
- Always use csrf_token in forms
- Use messages.success/error for user feedback

### Frontend & UI Rules
- Use Bootstrap 5 for all frontend layouts
- Use Font Awesome 6 for all icons
- Use Chart.js for graphs and reports
- Use DataTables for all list/table views with search and pagination
- Use Bootstrap cards with shadows for data display panels
- Use Bootstrap modals for create/edit forms
- Use gradient headers on cards and navbars for modern look
- Use toasts for success/error notifications
- Keep templates DRY — always use extends base.html and include tags
- All pages must have a consistent sidebar and topbar from base.html
- Color scheme: follow existing styles found in static/css/
- Never use inline styles — always use CSS classes


## 1. Folder Structure
```
./
  .env.example
  .gitattributes
  .gitignore
  .pre-commit-config.yaml
  CHANGELOG.md
  CLAUDE.md
  LICENSE
  README.md
  command-usages.txt
  docker-compose.yml
  generate_claude_md.py
  requirements-dev.txt
  requirements.txt
  .github/
  backend/
    db.sqlite3
    manage.py
    apps/
      accounts/
        __init__.py
        admin.py
        apps.py
        models.py
        serializers.py
        tests.py
        urls.py
        views.py
        migrations/
          0001_initial.py
          0002_rename_phone_number_user_phone_alter_user_timezone.py
          __init__.py
      ai_engine/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        providers/
          __init__.py
          ai_provider_factory.py
          base_ai_provider.py
          claude_provider.py
          mock_ai_provider.py
        repositories/
          __init__.py
          ai_repository.py
        services/
          __init__.py
          ai_service.py
          analysis_service.py
          prompt_service.py
      backtesting/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          backtest_repository.py
        services/
          __init__.py
          backtest_engine.py
          backtest_service.py
          report_service.py
      dashboard/
        __init__.py
        admin.py
        apps.py
        models.py
        serializers.py
        tests.py
        urls.py
        views.py
        migrations/
          __init__.py
      journal/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          journal_repository.py
        services/
          __init__.py
          ai_review_service.py
          journal_service.py
      knowledge/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          knowledge_repository.py
        services/
          __init__.py
          ai_summary_service.py
          knowledge_service.py
          search_service.py
      market_data/
        __init__.py
        admin.py
        apps.py
        constants.py
        models.py
        tests.py
        utils.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        indicators/
          __init__.py
          base_indicator.py
          indicator_service.py
          momentum.py
          moving_averages.py
          pivot.py
          volatility.py
          volume.py
        management/
          __init__.py
          commands/
            __init__.py
            import_instruments.py
        migrations/
          0001_initial.py
          0002_instrument_exchange_token_and_more.py
          0003_alter_instrument_options_instrument_instrument_type_and_more.py
          __init__.py
        providers/
          __init__.py
          base_provider.py
          mock_provider.py
          provider_factory.py
          zerodha_provider.py
        repositories/
          __init__.py
          candle_repository.py
          instrument_repository.py
          market_repository.py
          quote_repository.py
        services/
          __init__.py
          candle_service.py
          instrument_service.py
          market_service.py
          option_chain_service.py
          quote_service.py
          zerodha_service.py
      notifications/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          notification_repository.py
        services/
          __init__.py
          alert_service.py
          email_service.py
          notification_service.py
          telegram_service.py
      paper_trading/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          paper_repository.py
        services/
          __init__.py
          broker_simulator.py
          order_service.py
          portfolio_service.py
          position_service.py
      strategies/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          signal_repository.py
          strategy_repository.py
        services/
          __init__.py
          strategy_engine.py
          strategy_service.py
        strategies/
          __init__.py
          base_strategy.py
          ema_crossover.py
          orb_strategy.py
          rsi_strategy.py
          vwap_strategy.py
      zerodha/
        __init__.py
        admin.py
        apps.py
        models.py
        api/
          __init__.py
          serializers.py
          urls.py
          views.py
        migrations/
          0001_initial.py
          __init__.py
        repositories/
          __init__.py
          zerodha_repository.py
        services/
          __init__.py
          auth_service.py
          kite_service.py
          mcp_service.py
    config/
      __init__.py
      asgi.py
      urls.py
      wsgi.py
      settings/
        __init__.py
        base.py
        development.py
        production.py
    core/
      __init__.py
      authentication/
        __init__.py
      exceptions/
        __init__.py
      logging/
        __init__.py
      middleware/
        __init__.py
      security/
        __init__.py
      settings/
    data/
      instruments.csv
    infrastructure/
      __init__.py
      cache/
        __init__.py
      database/
        __init__.py
      messaging/
        __init__.py
      providers/
        __init__.py
      storage/
        __init__.py
    media/
    shared/
      __init__.py
      api_response.py
      pagination.py
      permissions.py
      constants/
        __init__.py
      enums/
        __init__.py
      helpers/
        __init__.py
      mixins/
        __init__.py
      models/
        __init__.py
        base_model.py
      repositories/
        __init__.py
        base_repository.py
      utils/
        __init__.py
    static/
      css/
      images/
      js/
      vendor/
    templates/
      base.html
  docker/
  docs/
    adr/
    ai/
    api/
    architecture/
    database/
    market-data/
    sprints/
  frontend/
    index.css
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
    src/
      App.jsx
      index.css
      main.jsx
      api/
        analysis.js
        auth.js
        axios.js
        backtesting.js
        journal.js
        knowledge.js
        market.js
        notifications.js
        paper.js
        strategies.js
        zerodha.js
      assets/
        icons/
        images/
      components/
        charts/
          CandleChart.jsx
          EquityCurveChart.jsx
          IndicatorChart.jsx
          PnLChart.jsx
          index.js
        common/
          Alert.jsx
          Badge.jsx
          Button.jsx
          Card.jsx
          EmptyState.jsx
          Input.jsx
          Modal.jsx
          Select.jsx
          Spinner.jsx
          Table.jsx
          index.js
        layout/
          AuthLayout.jsx
          PageWrapper.jsx
          Sidebar.jsx
          Topbar.jsx
          index.js
      hooks/
        useAuth.js
        useMarket.js
        useNotifications.js
        useWebSocket.js
      pages/
        analysis/
          Analysis.jsx
          SessionHistory.jsx
          components/
            AIResponseView.jsx
            AnalysisForm.jsx
            SignalCard.jsx
        auth/
          Login.jsx
        backtesting/
          BacktestResult.jsx
          Backtesting.jsx
          components/
            BacktestForm.jsx
            ResultStats.jsx
            TradeTable.jsx
        dashboard/
          Dashboard.jsx
          components/
            AISignalCard.jsx
            MarketSummaryCard.jsx
            PortfolioCard.jsx
            RecentSignalsTable.jsx
        journal/
          Journal.jsx
          JournalEntry.jsx
          Lessons.jsx
          components/
            AIReviewCard.jsx
            EntryForm.jsx
            LessonCard.jsx
            TradeNoteForm.jsx
        knowledge/
          ArticleDetail.jsx
          Knowledge.jsx
          Prompts.jsx
          Rules.jsx
          components/
            ArticleCard.jsx
            ArticleForm.jsx
            RuleCard.jsx
        market/
          Historical.jsx
          MarketWatch.jsx
          OptionChain.jsx
          components/
            IndexBar.jsx
            OptionChainTable.jsx
            QuoteCard.jsx
        notifications/
          Alerts.jsx
          Notifications.jsx
          Preferences.jsx
          components/
            AlertForm.jsx
            NotificationItem.jsx
        paper/
          Orders.jsx
          Portfolio.jsx
          Positions.jsx
          Trades.jsx
          components/
            OrderForm.jsx
            PortfolioStats.jsx
            PositionCard.jsx
        settings/
          Profile.jsx
          Settings.jsx
          components/
            ProfileForm.jsx
        strategies/
          Signals.jsx
          Strategies.jsx
          components/
            SignalTable.jsx
            StrategyCard.jsx
            StrategyForm.jsx
        zerodha/
          ZerodhaConnect.jsx
          ZerodhaOrders.jsx
          ZerodhaPositions.jsx
          components/
            ConnectionStatus.jsx
            FundsCard.jsx
      router/
        PrivateRoute.jsx
        index.jsx
      store/
        authStore.js
        marketStore.js
        notificationStore.js
        uiStore.js
      utils/
        constants.js
        formatters.js
        helpers.js
  scripts/
  tests/
```

## 2. Database Structure (Live MySQL — inspectdb)
```python
# No output from inspectdb
# stderr: C:\Users\RAnthony\source\repos\PythonProject\.venv\Scripts\python.exe: can't open file 'C:\\Users\\RAnthony\\source\\repos\\PythonProject\\athena-ai-trading-platform\\manage.py': [Errno 2] No such file or directory

```

## 3. Migration History
```
# No migrations found
```

## 4. All URL Endpoints
```
# django-extensions not installed — run: pip install django-extensions
# Then add 'django_extensions' to INSTALLED_APPS in settings.py
```

## 5. Installed Packages
```
altgraph==0.17.5
amqp==5.3.1
asgiref==3.11.1
attrs==26.1.0
billiard==4.2.4
celery==5.6.3
certifi==2026.4.22
cffi==2.0.0
charset-normalizer==3.4.7
click==8.4.2
click-didyoumean==0.3.1
click-plugins==1.1.1.2
click-repl==0.3.0
colorama==0.4.6
crispy-bootstrap5==2026.3
cron-descriptor==1.4.5
cryptography==48.0.0
diff-match-patch==20241021
Django==6.0.4
django-axes==8.3.1
django-celery-beat==2.9.0
django-ckeditor-5==0.2.20
django-cors-headers==4.9.0
django-crispy-forms==2.6
django-debug-toolbar==6.3.0
django-extensions==4.1
django-filter==25.2
django-import-export==4.4.1
django-timezone-field==7.2.2
django-widget-tweaks==1.5.1
django_celery_results==2.6.0
djangorestframework==3.17.1
djangorestframework_simplejwt==5.5.1
drf-spectacular==0.30.0
et_xmlfile==2.0.0
idna==3.13
inflection==0.5.1
iniconfig==2.3.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kombu==5.6.2
mysqlclient==2.2.8
numpy==2.4.4
openpyxl==3.1.5
packaging==26.2
pandas==3.0.2
pdfminer.six==20251230
pdfplumber==0.11.9
pefile==2024.8.26
pillow==12.2.0
pluggy==1.6.0
prompt_toolkit==3.0.52
psycopg==3.3.4
psycopg-binary==3.3.4
pycparser==3.0
Pygments==2.20.0
pyinstaller==6.20.0
pyinstaller-hooks-contrib==2026.6
PyJWT==2.13.0
pypdfium2==5.9.0
pytest==9.0.3
python-crontab==3.3.0
python-dateutil==2.9.0.post0
python-decouple==3.8
python-dotenv==1.2.2
pytz==2026.2
pywin32==312
pywin32-ctypes==0.2.3
PyYAML==6.0.3
redis==8.0.1
referencing==0.37.0
requests==2.33.1
rpds-py==2026.6.3
setuptools==82.0.1
six==1.17.0
sqlparse==0.5.5
structlog==26.1.0
tablib==3.9.0
tzdata==2026.2
tzlocal==5.4.4
uritemplate==4.2.0
urllib3==2.6.3
vine==5.1.0
wcwidth==0.8.2
whitenoise==6.12.0
xlsxwriter==3.2.9

```

## 6. Environment Variables (keys only — values hidden)
```
# No .env file found
```

## 7. Duplicate Function & Class Report
```
WARNING: Duplicate function 'validate' in:
    - .\backend\apps\accounts\serializers.py
    - .\backend\apps\backtesting\api\serializers.py
WARNING: Duplicate function 'get_provider' in:
    - .\backend\apps\ai_engine\providers\ai_provider_factory.py
    - .\backend\apps\market_data\providers\provider_factory.py
WARNING: Duplicate function 'complete' in:
    - .\backend\apps\ai_engine\providers\base_ai_provider.py
    - .\backend\apps\ai_engine\providers\claude_provider.py
    - .\backend\apps\ai_engine\providers\mock_ai_provider.py
    - .\backend\apps\ai_engine\services\ai_service.py
WARNING: Duplicate function 'get_by_type' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\strategies\repositories\strategy_repository.py
WARNING: Duplicate function 'get_by_name' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\strategies\repositories\strategy_repository.py
WARNING: Duplicate function 'get_today' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\services\journal_service.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\strategies\repositories\signal_repository.py
WARNING: Duplicate function 'get_by_instrument' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\market_data\repositories\quote_repository.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\strategies\repositories\signal_repository.py
WARNING: Duplicate function 'get_completed' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\backtesting\repositories\backtest_repository.py
WARNING: Duplicate function 'get_active' in:
    - .\backend\apps\ai_engine\repositories\ai_repository.py
    - .\backend\apps\notifications\repositories\notification_repository.py
WARNING: Duplicate function 'get_today_signals' in:
    - .\backend\apps\ai_engine\services\analysis_service.py
    - .\backend\apps\strategies\services\strategy_service.py
WARNING: Duplicate function 'get_by_user' in:
    - .\backend\apps\backtesting\repositories\backtest_repository.py
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
WARNING: Duplicate function 'get_by_id_for_user' in:
    - .\backend\apps\backtesting\repositories\backtest_repository.py
    - .\backend\apps\journal\repositories\journal_repository.py
WARNING: Duplicate function 'get_by_run' in:
    - .\backend\apps\backtesting\repositories\backtest_repository.py
    - .\backend\apps\backtesting\repositories\backtest_repository.py
WARNING: Duplicate function 'put' in:
    - .\backend\apps\journal\api\views.py
    - .\backend\apps\knowledge\api\views.py
    - .\backend\apps\knowledge\api\views.py
    - .\backend\apps\knowledge\api\views.py
    - .\backend\apps\notifications\api\views.py
    - .\backend\apps\strategies\api\views.py
    - .\backend\apps\zerodha\api\views.py
WARNING: Duplicate function 'get_by_date' in:
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\services\journal_service.py
WARNING: Duplicate function 'get_stats' in:
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\services\journal_service.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
WARNING: Duplicate function 'get_mistakes' in:
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\services\journal_service.py
WARNING: Duplicate function 'get_rules' in:
    - .\backend\apps\journal\repositories\journal_repository.py
    - .\backend\apps\journal\services\journal_service.py
    - .\backend\apps\knowledge\services\knowledge_service.py
WARNING: Duplicate function '_build_prompt' in:
    - .\backend\apps\journal\services\ai_review_service.py
    - .\backend\apps\knowledge\services\ai_summary_service.py
WARNING: Duplicate function 'get_by_slug' in:
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
WARNING: Duplicate function 'search' in:
    - .\backend\apps\knowledge\repositories\knowledge_repository.py
    - .\backend\apps\knowledge\services\knowledge_service.py
    - .\backend\apps\knowledge\services\search_service.py
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'is_index' in:
    - .\backend\apps\market_data\models.py
    - .\backend\apps\market_data\utils.py
WARNING: Duplicate function 'calculate' in:
    - .\backend\apps\market_data\indicators\base_indicator.py
    - .\backend\apps\market_data\indicators\indicator_service.py
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\pivot.py
    - .\backend\apps\market_data\indicators\pivot.py
    - .\backend\apps\market_data\indicators\volatility.py
    - .\backend\apps\market_data\indicators\volatility.py
    - .\backend\apps\market_data\indicators\volume.py
    - .\backend\apps\market_data\indicators\volume.py
WARNING: Duplicate function 'compute' in:
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\momentum.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\moving_averages.py
    - .\backend\apps\market_data\indicators\pivot.py
    - .\backend\apps\market_data\indicators\pivot.py
    - .\backend\apps\market_data\indicators\volatility.py
    - .\backend\apps\market_data\indicators\volatility.py
    - .\backend\apps\market_data\indicators\volume.py
    - .\backend\apps\market_data\indicators\volume.py
WARNING: Duplicate function 'get_quote' in:
    - .\backend\apps\market_data\providers\base_provider.py
    - .\backend\apps\market_data\providers\mock_provider.py
    - .\backend\apps\market_data\providers\zerodha_provider.py
    - .\backend\apps\market_data\services\quote_service.py
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_quotes' in:
    - .\backend\apps\market_data\providers\base_provider.py
    - .\backend\apps\market_data\providers\mock_provider.py
    - .\backend\apps\market_data\providers\zerodha_provider.py
    - .\backend\apps\market_data\services\quote_service.py
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_historical_data' in:
    - .\backend\apps\market_data\providers\base_provider.py
    - .\backend\apps\market_data\providers\mock_provider.py
    - .\backend\apps\market_data\providers\zerodha_provider.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_option_chain' in:
    - .\backend\apps\market_data\providers\base_provider.py
    - .\backend\apps\market_data\providers\mock_provider.py
    - .\backend\apps\market_data\providers\zerodha_provider.py
WARNING: Duplicate function 'get_latest' in:
    - .\backend\apps\market_data\repositories\candle_repository.py
    - .\backend\apps\market_data\services\candle_service.py
WARNING: Duplicate function 'get_range' in:
    - .\backend\apps\market_data\repositories\candle_repository.py
    - .\backend\apps\market_data\services\candle_service.py
WARNING: Duplicate function 'get_by_symbol' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\repositories\quote_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_by_token' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\repositories\quote_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_by_exchange' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_indices' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_options' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_futures' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_by_expiry' in:
    - .\backend\apps\market_data\repositories\instrument_repository.py
    - .\backend\apps\market_data\services\instrument_service.py
WARNING: Duplicate function 'get_all' in:
    - .\backend\apps\market_data\services\instrument_service.py
    - .\backend\apps\market_data\services\market_service.py
    - .\backend\apps\strategies\services\strategy_service.py
WARNING: Duplicate function 'get_historical' in:
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
WARNING: Duplicate function 'get_positions' in:
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_holdings' in:
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_orders' in:
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\paper_trading\services\order_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_funds' in:
    - .\backend\apps\market_data\services\zerodha_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_for_user' in:
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\zerodha\repositories\zerodha_repository.py
WARNING: Duplicate function 'get_or_create_for_user' in:
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\zerodha\repositories\zerodha_repository.py
WARNING: Duplicate function 'get_unread_count' in:
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\notifications\services\notification_service.py
WARNING: Duplicate function 'mark_read' in:
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\notifications\services\notification_service.py
WARNING: Duplicate function 'mark_all_read' in:
    - .\backend\apps\notifications\repositories\notification_repository.py
    - .\backend\apps\notifications\services\notification_service.py
WARNING: Duplicate function 'send' in:
    - .\backend\apps\notifications\services\email_service.py
    - .\backend\apps\notifications\services\notification_service.py
    - .\backend\apps\notifications\services\telegram_service.py
WARNING: Duplicate function 'send_price_alert' in:
    - .\backend\apps\notifications\services\email_service.py
    - .\backend\apps\notifications\services\telegram_service.py
WARNING: Duplicate function 'send_daily_summary' in:
    - .\backend\apps\notifications\services\email_service.py
    - .\backend\apps\notifications\services\telegram_service.py
WARNING: Duplicate function 'get_by_account' in:
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\paper_trading\repositories\paper_repository.py
WARNING: Duplicate function 'get_open_positions' in:
    - .\backend\apps\paper_trading\repositories\paper_repository.py
    - .\backend\apps\paper_trading\services\position_service.py
WARNING: Duplicate function 'place_order' in:
    - .\backend\apps\paper_trading\services\order_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'cancel_order' in:
    - .\backend\apps\paper_trading\services\order_service.py
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'get_active_signals' in:
    - .\backend\apps\strategies\repositories\signal_repository.py
    - .\backend\apps\strategies\services\strategy_service.py
WARNING: Duplicate function 'get_enabled' in:
    - .\backend\apps\strategies\repositories\strategy_repository.py
    - .\backend\apps\strategies\services\strategy_service.py
WARNING: Duplicate function 'run_all' in:
    - .\backend\apps\strategies\services\strategy_engine.py
    - .\backend\apps\strategies\services\strategy_service.py
WARNING: Duplicate function 'get_by_id' in:
    - .\backend\apps\strategies\services\strategy_service.py
    - .\backend\shared\repositories\base_repository.py
WARNING: Duplicate function 'create' in:
    - .\backend\apps\strategies\services\strategy_service.py
    - .\backend\shared\repositories\base_repository.py
WARNING: Duplicate function 'update' in:
    - .\backend\apps\strategies\services\strategy_service.py
    - .\backend\shared\repositories\base_repository.py
WARNING: Duplicate function 'evaluate' in:
    - .\backend\apps\strategies\strategies\base_strategy.py
    - .\backend\apps\strategies\strategies\ema_crossover.py
    - .\backend\apps\strategies\strategies\orb_strategy.py
    - .\backend\apps\strategies\strategies\rsi_strategy.py
    - .\backend\apps\strategies\strategies\vwap_strategy.py
WARNING: Duplicate function 'minimum_candles_required' in:
    - .\backend\apps\strategies\strategies\base_strategy.py
    - .\backend\apps\strategies\strategies\ema_crossover.py
    - .\backend\apps\strategies\strategies\orb_strategy.py
    - .\backend\apps\strategies\strategies\rsi_strategy.py
    - .\backend\apps\strategies\strategies\vwap_strategy.py
WARNING: Duplicate function 'get_profile' in:
    - .\backend\apps\zerodha\services\kite_service.py
    - .\backend\apps\zerodha\services\mcp_service.py
WARNING: Duplicate function 'has_permission' in:
    - .\backend\shared\permissions.py
    - .\backend\shared\permissions.py
WARNING: Duplicate class 'Meta' in:
    - .\backend\apps\accounts\models.py
    - .\backend\apps\accounts\serializers.py
    - .\backend\apps\ai_engine\models.py
    - .\backend\apps\ai_engine\models.py
    - .\backend\apps\ai_engine\models.py
    - .\backend\apps\ai_engine\api\serializers.py
    - .\backend\apps\ai_engine\api\serializers.py
    - .\backend\apps\ai_engine\api\serializers.py
    - .\backend\apps\backtesting\models.py
    - .\backend\apps\backtesting\models.py
    - .\backend\apps\backtesting\models.py
    - .\backend\apps\backtesting\api\serializers.py
    - .\backend\apps\backtesting\api\serializers.py
    - .\backend\apps\backtesting\api\serializers.py
    - .\backend\apps\backtesting\api\serializers.py
    - .\backend\apps\journal\models.py
    - .\backend\apps\journal\models.py
    - .\backend\apps\journal\models.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\journal\api\serializers.py
    - .\backend\apps\knowledge\models.py
    - .\backend\apps\knowledge\models.py
    - .\backend\apps\knowledge\models.py
    - .\backend\apps\knowledge\models.py
    - .\backend\apps\knowledge\models.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\knowledge\api\serializers.py
    - .\backend\apps\market_data\models.py
    - .\backend\apps\market_data\models.py
    - .\backend\apps\market_data\models.py
    - .\backend\apps\market_data\api\serializers.py
    - .\backend\apps\market_data\api\serializers.py
    - .\backend\apps\notifications\models.py
    - .\backend\apps\notifications\models.py
    - .\backend\apps\notifications\models.py
    - .\backend\apps\notifications\api\serializers.py
    - .\backend\apps\notifications\api\serializers.py
    - .\backend\apps\notifications\api\serializers.py
    - .\backend\apps\notifications\api\serializers.py
    - .\backend\apps\paper_trading\models.py
    - .\backend\apps\paper_trading\models.py
    - .\backend\apps\paper_trading\models.py
    - .\backend\apps\paper_trading\models.py
    - .\backend\apps\paper_trading\api\serializers.py
    - .\backend\apps\paper_trading\api\serializers.py
    - .\backend\apps\paper_trading\api\serializers.py
    - .\backend\apps\paper_trading\api\serializers.py
    - .\backend\apps\strategies\models.py
    - .\backend\apps\strategies\models.py
    - .\backend\apps\strategies\api\serializers.py
    - .\backend\apps\strategies\api\serializers.py
    - .\backend\apps\strategies\api\serializers.py
    - .\backend\apps\zerodha\models.py
    - .\backend\apps\zerodha\models.py
    - .\backend\apps\zerodha\api\serializers.py
    - .\backend\apps\zerodha\api\serializers.py
    - .\backend\shared\models\base_model.py
WARNING: Duplicate class 'ZerodhaConfig' in:
    - .\backend\apps\zerodha\apps.py
    - .\backend\apps\zerodha\models.py
```

## 8. Django Python Files

### .\requirements.txt
```python
Django>=5.2,<6.0
djangorestframework>=3.16
djangorestframework-simplejwt>=5.5
django-filter>=25.1
drf-spectacular>=0.28
django-cors-headers>=4.7
python-dotenv>=1.1
psycopg[binary]>=3.2
redis>=6.2
celery>=5.5
whitenoise>=6.9
gunicorn>=23.0
Pillow>=11.3
requests>=2.32
httpx>=0.28
pydantic>=2.11
structlog>=25.4
pytest>=8.4
pytest-django>=4.11
coverage>=7.10
black>=25.1
isort>=6.0
flake8>=7.3
mypy>=1.17
channels==4.2.0
channels-redis==4.2.0
daphne==4.1.2
```

### .\backend\apps\accounts\admin.py
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass
```

### .\backend\apps\accounts\apps.py
```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
```

### .\backend\apps\accounts\models.py
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

from shared.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User Model
    """

    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kolkata",
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
```

### .\backend\apps\accounts\serializers.py
```python
from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "timezone",
        ]
```

### .\backend\apps\accounts\urls.py
```python
from django.urls import path
from .views import LoginAPIView, LogoutAPIView, ProfileAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]
```

### .\backend\apps\accounts\views.py
```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "success": True,
                    "message": "Logout successful.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Invalid refresh token.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
```

### .\backend\apps\ai_engine\admin.py
```python
from django.contrib import admin

from .models import AISignal, AnalysisSession, PromptTemplate


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "template_type",
        "model",
        "version",
        "is_default",
        "is_active",
    )
    list_filter = ("template_type", "model", "is_default")
    search_fields = ("name",)


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):

    list_display = (
        "session_type",
        "instrument",
        "status",
        "model_used",
        "tokens_used",
        "duration_ms",
        "session_time",
    )
    list_filter = ("session_type", "status")
    search_fields = ("instrument__symbol",)
    readonly_fields = (
        "prompt_used",
        "ai_response",
        "parsed_output",
        "market_context",
        "tokens_used",
        "duration_ms",
        "session_time",
    )


@admin.register(AISignal)
class AISignalAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "signal",
        "confidence",
        "confidence_score",
        "price_at_signal",
        "signal_time",
    )
    list_filter = ("signal", "confidence")
    search_fields = ("instrument__symbol",)
```

### .\backend\apps\ai_engine\apps.py
```python
from django.apps import AppConfig


class AiEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_engine"
```

### .\backend\apps\ai_engine\models.py
```python
from django.db import models

from apps.market_data.models import Instrument
from shared.models import BaseModel


class PromptTemplate(BaseModel):
    """
    Stores reusable prompt templates for AI analysis.
    Templates use placeholders replaced at runtime.
    """

    TEMPLATE_TYPE_CHOICES = [
        ("MARKET_ANALYSIS", "Market Analysis"),
        ("SETUP_SCANNER", "Setup Scanner"),
        ("OPTION_CHAIN", "Option Chain Analysis"),
        ("RISK_ASSESSMENT", "Risk Assessment"),
        ("TRADE_REVIEW", "Trade Review"),
        ("NEWS_ANALYSIS", "News Analysis"),
    ]

    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        db_index=True,
    )
    system_prompt = models.TextField(
        help_text="System prompt sent to the AI model.",
    )
    user_prompt_template = models.TextField(
        help_text="User prompt template with {placeholders}.",
    )
    model = models.CharField(
        max_length=50,
        default="claude-sonnet-4-6",
        help_text="AI model to use for this template.",
    )
    max_tokens = models.IntegerField(default=2000)
    temperature = models.FloatField(default=0.3)
    version = models.CharField(max_length=20, default="v1")
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "ai_prompt_templates"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.template_type})"


class AnalysisSession(BaseModel):
    """
    Records a complete AI analysis session.
    Stores input, output, and metadata for journaling and backtesting.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETE", "Complete"),
        ("FAILED", "Failed"),
    ]

    SESSION_TYPE_CHOICES = [
        ("MARKET_ANALYSIS", "Market Analysis"),
        ("SETUP_SCANNER", "Setup Scanner"),
        ("OPTION_CHAIN", "Option Chain Analysis"),
        ("RISK_ASSESSMENT", "Risk Assessment"),
        ("TRADE_REVIEW", "Trade Review"),
    ]

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analysis_sessions",
    )
    template = models.ForeignKey(
        PromptTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        db_index=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    # Input
    timeframe = models.CharField(max_length=10, blank=True)
    market_context = models.JSONField(
        default=dict,
        help_text="Market data snapshot used as input.",
    )
    prompt_used = models.TextField(blank=True)

    # Output
    ai_response = models.TextField(blank=True)
    parsed_output = models.JSONField(
        default=dict,
        help_text="Structured output parsed from AI response.",
    )

    # Metadata
    model_used = models.CharField(max_length=50, blank=True)
    tokens_used = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    session_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "ai_analysis_sessions"
        ordering = ["-session_time"]
        indexes = [
            models.Index(fields=["session_type", "session_time"]),
            models.Index(fields=["status", "session_time"]),
        ]

    def __str__(self) -> str:
        symbol = self.instrument.symbol if self.instrument else "N/A"
        return f"{self.session_type} | {symbol} | {self.status}"


class AISignal(BaseModel):
    """
    A trading signal generated by the AI engine.
    Distinct from strategy signals — these are AI-reasoned outputs.
    """

    SIGNAL_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
        ("NEUTRAL", "Neutral"),
        ("NO_SETUP", "No Setup"),
        ("WATCH", "Watch"),
    ]

    CONFIDENCE_CHOICES = [
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
    ]

    session = models.OneToOneField(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name="ai_signal",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="ai_signals",
    )

    signal = models.CharField(
        max_length=10,
        choices=SIGNAL_CHOICES,
        db_index=True,
    )
    confidence = models.CharField(
        max_length=10,
        choices=CONFIDENCE_CHOICES,
        default="MEDIUM",
    )
    confidence_score = models.IntegerField(
        default=0,
        help_text="0-100 confidence score.",
    )

    price_at_signal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    target_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stop_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    reasoning = models.TextField(
        help_text="AI reasoning for this signal.",
    )
    key_levels = models.JSONField(default=dict)
    risks = models.JSONField(default=list)
    signal_time = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "ai_signals"
        ordering = ["-signal_time"]

    def __str__(self) -> str:
        return (
            f"{self.instrument.symbol} | "
            f"{self.signal} | "
            f"{self.confidence} | "
            f"{self.confidence_score}%"
        )
```

### .\backend\apps\ai_engine\api\serializers.py
```python
from rest_framework import serializers

from ..models import AISignal, AnalysisSession, PromptTemplate


class PromptTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PromptTemplate
        fields = [
            "id",
            "name",
            "template_type",
            "model",
            "max_tokens",
            "temperature",
            "version",
            "is_default",
            "is_active",
        ]


class AnalysisSessionSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    template_name = serializers.CharField(
        source="template.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AnalysisSession
        fields = [
            "id",
            "symbol",
            "template_name",
            "session_type",
            "status",
            "timeframe",
            "model_used",
            "tokens_used",
            "duration_ms",
            "parsed_output",
            "ai_response",
            "session_time",
        ]


class AISignalSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = AISignal
        fields = [
            "id",
            "symbol",
            "signal",
            "confidence",
            "confidence_score",
            "price_at_signal",
            "target_price",
            "stop_loss",
            "reasoning",
            "key_levels",
            "risks",
            "signal_time",
        ]


class AnalysisRequestSerializer(serializers.Serializer):
    """Request body for triggering an analysis."""
    symbol = serializers.CharField()
    timeframe = serializers.ChoiceField(
        choices=["1m", "3m", "5m", "15m", "30m", "1h", "1d"],
        default="15m",
    )
    session_type = serializers.ChoiceField(
        choices=[
            "MARKET_ANALYSIS",
            "SETUP_SCANNER",
            "OPTION_CHAIN",
            "RISK_ASSESSMENT",
            "TRADE_REVIEW",
        ],
        default="MARKET_ANALYSIS",
    )
    persist = serializers.BooleanField(default=True)
```

### .\backend\apps\ai_engine\api\urls.py
```python
from django.urls import path

from .views import (
    AISignalListAPIView,
    AnalysisRunAPIView,
    AnalysisSessionDetailAPIView,
    AnalysisSessionListAPIView,
    PromptTemplateListAPIView,
)

urlpatterns = [
    path(
        "analyze/",
        AnalysisRunAPIView.as_view(),
        name="ai-analyze",
    ),
    path(
        "sessions/",
        AnalysisSessionListAPIView.as_view(),
        name="ai-sessions",
    ),
    path(
        "sessions/<int:pk>/",
        AnalysisSessionDetailAPIView.as_view(),
        name="ai-session-detail",
    ),
    path(
        "signals/",
        AISignalListAPIView.as_view(),
        name="ai-signals",
    ),
    path(
        "templates/",
        PromptTemplateListAPIView.as_view(),
        name="ai-templates",
    ),
]
```

### .\backend\apps\ai_engine\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.analysis_service import AnalysisService
from .serializers import (
    AISignalSerializer,
    AnalysisRequestSerializer,
    AnalysisSessionSerializer,
    PromptTemplateSerializer,
)

logger = logging.getLogger(__name__)


class AnalysisRunAPIView(APIView):
    """
    POST /api/ai/analyze/
    Run a full AI market analysis for a symbol.

    Request body:
        {
            "symbol": "NIFTY",
            "timeframe": "15m",
            "session_type": "MARKET_ANALYSIS",
            "persist": true
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnalysisRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            service = AnalysisService()
            result = service.analyze(
                symbol=serializer.validated_data["symbol"].upper(),
                timeframe=serializer.validated_data["timeframe"],
                session_type=serializer.validated_data["session_type"],
                persist=serializer.validated_data["persist"],
            )
            return ApiResponse.success(data=result)
        except Exception as e:
            logger.error(f"AnalysisRunAPIView error: {e}")
            return ApiResponse.error(message="Analysis failed.")


class AnalysisSessionListAPIView(APIView):
    """
    GET /api/ai/sessions/
    Return today's analysis sessions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = AnalysisService.get_today_sessions()
        serializer = AnalysisSessionSerializer(sessions, many=True)
        return ApiResponse.success(serializer.data)


class AnalysisSessionDetailAPIView(APIView):
    """
    GET /api/ai/sessions/<id>/
    Return a single analysis session with full AI response.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        session = AnalysisService.get_session(pk)

        if not session:
            return ApiResponse.error(message="Session not found.")

        serializer = AnalysisSessionSerializer(session)
        return ApiResponse.success(serializer.data)


class AISignalListAPIView(APIView):
    """
    GET /api/ai/signals/
    Return today's AI signals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        signals = AnalysisService.get_today_signals()
        serializer = AISignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)


class PromptTemplateListAPIView(APIView):
    """
    GET /api/ai/templates/
    Return all prompt templates.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ..repositories.ai_repository import PromptTemplateRepository
        templates = PromptTemplateRepository.active()
        serializer = PromptTemplateSerializer(templates, many=True)
        return ApiResponse.success(serializer.data)
```

### .\backend\apps\backtesting\admin.py
```python
from django.contrib import admin

from .models import BacktestResult, BacktestRun, BacktestTrade


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):

    list_display = (
        "strategy",
        "instrument",
        "timeframe",
        "from_date",
        "to_date",
        "status",
        "candles_processed",
        "duration_seconds",
        "created_at",
    )
    list_filter = ("status", "timeframe")
    search_fields = ("strategy__name", "instrument__symbol")
    readonly_fields = (
        "status",
        "started_at",
        "completed_at",
        "duration_seconds",
        "candles_processed",
        "error_message",
    )


@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):

    list_display = (
        "run",
        "direction",
        "entry_price",
        "exit_price",
        "pnl",
        "net_pnl",
        "exit_reason",
        "entry_time",
    )
    list_filter = ("direction", "exit_reason", "signal")


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):

    list_display = (
        "run",
        "total_trades",
        "win_rate",
        "total_return_pct",
        "max_drawdown_pct",
        "sharpe_ratio",
        "profit_factor",
    )
    readonly_fields = (
        "equity_curve",
    )
```

### .\backend\apps\backtesting\apps.py
```python
from django.apps import AppConfig


class BacktestingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.backtesting"
```

### .\backend\apps\backtesting\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from apps.strategies.models import Strategy
from shared.models import BaseModel

User = get_user_model()


class BacktestRun(BaseModel):
    """
    A backtesting run configuration and execution record.
    Defines what strategy, symbol, timeframe, and date range to test.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETE", "Complete"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="backtest_runs",
    )

    # Configuration
    timeframe = models.CharField(max_length=10)
    from_date = models.DateField()
    to_date = models.DateField()
    initial_capital = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=100000.00,
    )
    position_size_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Percentage of capital per trade.",
    )
    brokerage_per_trade = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=20.00,
    )

    # Execution
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(default=0)
    error_message = models.TextField(blank=True)
    candles_processed = models.IntegerField(default=0)

    class Meta:
        db_table = "backtest_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["strategy", "instrument"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.strategy.name} | "
            f"{self.instrument.symbol} | "
            f"{self.from_date} → {self.to_date} | "
            f"{self.status}"
        )


class BacktestTrade(BaseModel):
    """
    A single trade executed during a backtest run.
    Records entry, exit, PnL, and signal context.
    """

    DIRECTION_CHOICES = [
        ("LONG", "Long"),
        ("SHORT", "Short"),
    ]

    run = models.ForeignKey(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name="trades",
    )

    direction = models.CharField(
        max_length=5,
        choices=DIRECTION_CHOICES,
    )
    quantity = models.IntegerField(default=1)

    entry_price = models.DecimalField(max_digits=12, decimal_places=2)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField()

    pnl = models.DecimalField(max_digits=12, decimal_places=2)
    pnl_pct = models.DecimalField(max_digits=8, decimal_places=4)
    brokerage = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    net_pnl = models.DecimalField(max_digits=12, decimal_places=2)

    # Signal context at entry
    signal = models.CharField(max_length=10)
    signal_strength = models.CharField(max_length=10, blank=True)
    signal_notes = models.TextField(blank=True)
    signal_context = models.JSONField(default=dict)

    # Exit reason
    exit_reason = models.CharField(
        max_length=20,
        choices=[
            ("SIGNAL", "Opposite Signal"),
            ("STOP_LOSS", "Stop Loss"),
            ("TARGET", "Target Hit"),
            ("EOD", "End of Day"),
            ("END_OF_DATA", "End of Data"),
        ],
        default="SIGNAL",
    )

    # Running capital after this trade
    capital_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    class Meta:
        db_table = "backtest_trades"
        ordering = ["entry_time"]
        indexes = [
            models.Index(fields=["run", "entry_time"]),
        ]

    def __str__(self) -> str:
        result = "WIN" if float(self.pnl) > 0 else "LOSS"
        return (
            f"{result} | {self.direction} @ "
            f"{self.entry_price} → {self.exit_price} | "
            f"₹{self.net_pnl}"
        )


class BacktestResult(BaseModel):
    """
    Aggregated statistics for a completed backtest run.
    One result per run.
    """

    run = models.OneToOneField(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name="result",
    )

    # Trade statistics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )

    # PnL statistics
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_pnl_per_trade = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_win = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    largest_win = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    largest_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_factor = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Capital statistics
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    final_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return_pct = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_drawdown_pct = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Risk statistics
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    expectancy = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    risk_reward_ratio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    consecutive_wins = models.IntegerField(default=0)
    consecutive_losses = models.IntegerField(default=0)

    # Equity curve (stored as JSON list)
    equity_curve = models.JSONField(
        default=list,
        help_text="List of {time, capital} dicts for plotting.",
    )

    class Meta:
        db_table = "backtest_results"

    def __str__(self) -> str:
        return (
            f"{self.run.strategy.name} | "
            f"WR: {self.win_rate}% | "
            f"Return: {self.total_return_pct}%"
        )
```

### .\backend\apps\backtesting\api\serializers.py
```python
from rest_framework import serializers

from ..models import BacktestResult, BacktestRun, BacktestTrade


class BacktestRunSerializer(serializers.ModelSerializer):

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = BacktestRun
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "timeframe",
            "from_date",
            "to_date",
            "initial_capital",
            "position_size_pct",
            "brokerage_per_trade",
            "status",
            "candles_processed",
            "duration_seconds",
            "started_at",
            "completed_at",
            "error_message",
            "created_at",
        ]


class BacktestCreateSerializer(serializers.Serializer):
    """Request body for creating a backtest run."""
    strategy_id = serializers.IntegerField()
    symbol = serializers.CharField()
    timeframe = serializers.ChoiceField(
        choices=["1m", "3m", "5m", "15m", "30m", "1h", "1d"],
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    initial_capital = serializers.FloatField(default=100000)
    position_size_pct = serializers.FloatField(default=10)
    brokerage_per_trade = serializers.FloatField(default=20)

    def validate(self, attrs):
        if attrs["from_date"] >= attrs["to_date"]:
            raise serializers.ValidationError(
                "from_date must be before to_date."
            )
        return attrs


class BacktestTradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = BacktestTrade
        fields = [
            "id",
            "direction",
            "quantity",
            "entry_price",
            "exit_price",
            "entry_time",
            "exit_time",
            "pnl",
            "pnl_pct",
            "brokerage",
            "net_pnl",
            "signal",
            "signal_strength",
            "exit_reason",
            "capital_after",
        ]


class BacktestResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = BacktestResult
        fields = [
            "id",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "total_pnl",
            "total_net_pnl",
            "avg_pnl_per_trade",
            "avg_win",
            "avg_loss",
            "largest_win",
            "largest_loss",
            "profit_factor",
            "initial_capital",
            "final_capital",
            "total_return_pct",
            "max_drawdown",
            "max_drawdown_pct",
            "sharpe_ratio",
            "expectancy",
            "risk_reward_ratio",
            "consecutive_wins",
            "consecutive_losses",
            "equity_curve",
        ]


class BacktestRunDetailSerializer(serializers.ModelSerializer):
    """Full detail including result."""

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    result = BacktestResultSerializer(read_only=True)

    class Meta:
        model = BacktestRun
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "timeframe",
            "from_date",
            "to_date",
            "initial_capital",
            "position_size_pct",
            "status",
            "candles_processed",
            "duration_seconds",
            "result",
            "created_at",
        ]
```

### .\backend\apps\backtesting\api\urls.py
```python
from django.urls import path

from .views import (
    BacktestRunDetailAPIView,
    BacktestRunListAPIView,
    BacktestTradeListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    path(
        "runs/",
        BacktestRunListAPIView.as_view(),
        name="backtest-runs",
    ),
    path(
        "runs/<int:pk>/",
        BacktestRunDetailAPIView.as_view(),
        name="backtest-run-detail",
    ),

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------
    path(
        "runs/<int:pk>/trades/",
        BacktestTradeListAPIView.as_view(),
        name="backtest-trades",
    ),
]
```

### .\backend\apps\backtesting\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.backtest_service import BacktestService
from .serializers import (
    BacktestCreateSerializer,
    BacktestRunDetailSerializer,
    BacktestRunSerializer,
    BacktestTradeSerializer,
)

logger = logging.getLogger(__name__)


class BacktestRunListAPIView(APIView):
    """
    GET  /api/backtest/runs/  — list runs
    POST /api/backtest/runs/  — create and execute run
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 20))
            runs = BacktestService.get_runs(request.user, limit)
            serializer = BacktestRunSerializer(runs, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"BacktestRunListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch backtest runs.")

    def post(self, request):
        serializer = BacktestCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            # Create run
            run = BacktestService.create_run(
                user=request.user,
                data=serializer.validated_data,
            )

            # Execute synchronously
            result = BacktestService.execute(run)

            return ApiResponse.success(
                data=result,
                message="Backtest complete.",
            )

        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"BacktestRunListAPIView POST error: {e}")
            return ApiResponse.error(message="Backtest failed.")


class BacktestRunDetailAPIView(APIView):
    """
    GET /api/backtest/runs/<id>/
    Return full backtest run with result.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        run = BacktestService.get_run(request.user, pk)

        if not run:
            return ApiResponse.error(message="Backtest run not found.")

        serializer = BacktestRunDetailSerializer(run)
        return ApiResponse.success(serializer.data)


class BacktestTradeListAPIView(APIView):
    """
    GET /api/backtest/runs/<id>/trades/
    Return all trades for a backtest run.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        run = BacktestService.get_run(request.user, pk)

        if not run:
            return ApiResponse.error(message="Backtest run not found.")

        try:
            trades = BacktestService.get_trades(run)
            serializer = BacktestTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"BacktestTradeListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch trades.")
```

### .\backend\apps\dashboard\admin.py
```python
from django.contrib import admin

# Register your models here.

```

### .\backend\apps\dashboard\apps.py
```python
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"

```

### .\backend\apps\dashboard\models.py
```python
from django.db import models

# Create your models here.

```

### .\backend\apps\dashboard\serializers.py
```python
from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    application = serializers.CharField()
    version = serializers.CharField()
    status = serializers.CharField()
    user = serializers.DictField()
    modules = serializers.DictField()
```

### .\backend\apps\dashboard\urls.py
```python
from django.urls import path
from .views import DashboardAPIView

urlpatterns = [
    path("", DashboardAPIView.as_view(), name="dashboard"),
]
```

### .\backend\apps\dashboard\views.py
```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse


class DashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = {
            "application": "Athena AI Trading Platform",
            "version": "1.0.0",
            "status": "Running",
            "user": {
                "username": request.user.username,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
            },
            "modules": {
                "dashboard": True,
                "market_data": True,
                "paper_trading": True,
                "backtesting": True,
                "ai_engine": True,
                "strategies": True,
                "journal": True,
                "notifications": True,
                "knowledge": True,
            },
        }

        return ApiResponse.success(data=data)
```

### .\backend\apps\journal\admin.py
```python
from django.contrib import admin

from .models import JournalEntry, Lesson, TradeNote


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "date",
        "session",
        "market_bias",
        "mood",
        "trades_taken",
        "total_pnl",
        "rating",
    )
    list_filter = ("session", "market_bias", "mood")
    search_fields = ("user__username", "title")
    readonly_fields = ("ai_review", "ai_reviewed_at")


@admin.register(TradeNote)
class TradeNoteAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "outcome",
        "pnl",
        "followed_plan",
        "mistake_type",
        "created_at",
    )
    list_filter = ("outcome", "followed_plan", "mistake_type")
    search_fields = ("instrument__symbol",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "title",
        "category",
        "is_rule",
        "times_reinforced",
        "created_at",
    )
    list_filter = ("category", "is_rule")
    search_fields = ("title", "content")
```

### .\backend\apps\journal\apps.py
```python
from django.apps import AppConfig


class JournalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.journal"
```

### .\backend\apps\journal\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from apps.paper_trading.models import PaperTrade
from shared.models import BaseModel

User = get_user_model()


class JournalEntry(BaseModel):
    """
    A daily trading journal entry.
    Records market observations, trades, emotions, and lessons.
    """

    MOOD_CHOICES = [
        ("CONFIDENT", "Confident"),
        ("NEUTRAL", "Neutral"),
        ("ANXIOUS", "Anxious"),
        ("FEARFUL", "Fearful"),
        ("GREEDY", "Greedy"),
        ("DISCIPLINED", "Disciplined"),
    ]

    SESSION_CHOICES = [
        ("PRE_MARKET", "Pre Market"),
        ("INTRADAY", "Intraday"),
        ("POST_MARKET", "Post Market"),
        ("EOD", "End of Day"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )

    date = models.DateField(db_index=True)
    session = models.CharField(
        max_length=15,
        choices=SESSION_CHOICES,
        default="EOD",
    )
    title = models.CharField(max_length=200)

    # Market observations
    market_bias = models.CharField(
        max_length=10,
        choices=[
            ("BULLISH", "Bullish"),
            ("BEARISH", "Bearish"),
            ("NEUTRAL", "Neutral"),
        ],
        blank=True,
    )
    market_notes = models.TextField(
        blank=True,
        help_text="Market structure, key levels, observations.",
    )

    # Trade summary
    trades_taken = models.IntegerField(default=0)
    winners = models.IntegerField(default=0)
    losers = models.IntegerField(default=0)
    total_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Psychology
    mood = models.CharField(
        max_length=15,
        choices=MOOD_CHOICES,
        blank=True,
    )
    emotion_notes = models.TextField(
        blank=True,
        help_text="Emotional state and psychological observations.",
    )

    # Lessons
    what_worked = models.TextField(blank=True)
    what_didnt_work = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    tomorrow_plan = models.TextField(blank=True)

    # AI Review
    ai_review = models.TextField(
        blank=True,
        help_text="AI-generated review of the journal entry.",
    )
    ai_reviewed_at = models.DateTimeField(null=True, blank=True)

    # Rating
    rating = models.IntegerField(
        default=0,
        help_text="Self-rating for the day 1-10.",
    )

    class Meta:
        db_table = "journal_entries"
        ordering = ["-date"]
        unique_together = [("user", "date", "session")]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} | {self.date} | {self.session}"


class TradeNote(BaseModel):
    """
    Detailed notes attached to a specific trade.
    Links a journal entry to a paper trade with analysis.
    """

    OUTCOME_CHOICES = [
        ("WIN", "Win"),
        ("LOSS", "Loss"),
        ("BREAKEVEN", "Breakeven"),
    ]

    MISTAKE_CHOICES = [
        ("NONE", "No Mistake"),
        ("EARLY_ENTRY", "Early Entry"),
        ("LATE_ENTRY", "Late Entry"),
        ("EARLY_EXIT", "Early Exit"),
        ("LATE_EXIT", "Late Exit"),
        ("OVERSIZE", "Oversized Position"),
        ("NO_SL", "No Stop Loss"),
        ("REVENGE", "Revenge Trade"),
        ("FOMO", "FOMO Trade"),
        ("PLAN_DEVIATION", "Deviated from Plan"),
    ]

    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="trade_notes",
    )
    trade = models.OneToOneField(
        PaperTrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_note",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Trade details
    setup_description = models.TextField(
        help_text="Describe the setup that triggered this trade.",
    )
    entry_reason = models.TextField(blank=True)
    exit_reason = models.TextField(blank=True)

    outcome = models.CharField(
        max_length=10,
        choices=OUTCOME_CHOICES,
        blank=True,
    )
    pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # Analysis
    followed_plan = models.BooleanField(default=True)
    mistake_type = models.CharField(
        max_length=20,
        choices=MISTAKE_CHOICES,
        default="NONE",
    )
    mistake_notes = models.TextField(blank=True)
    improvement = models.TextField(
        blank=True,
        help_text="What would you do differently?",
    )

    # Screenshot
    screenshot_url = models.URLField(blank=True)

    class Meta:
        db_table = "journal_trade_notes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        symbol = self.instrument.symbol if self.instrument else "N/A"
        return f"{symbol} | {self.outcome} | ₹{self.pnl}"


class Lesson(BaseModel):
    """
    A trading lesson extracted from journal entries.
    Builds a personal knowledge base over time.
    """

    CATEGORY_CHOICES = [
        ("ENTRY", "Entry Rules"),
        ("EXIT", "Exit Rules"),
        ("RISK", "Risk Management"),
        ("PSYCHOLOGY", "Psychology"),
        ("STRATEGY", "Strategy"),
        ("MARKET", "Market Observation"),
        ("GENERAL", "General"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        default="GENERAL",
        db_index=True,
    )

    times_reinforced = models.IntegerField(
        default=1,
        help_text="How many times this lesson was relearned.",
    )
    is_rule = models.BooleanField(
        default=False,
        help_text="Mark as a hard trading rule.",
    )

    class Meta:
        db_table = "journal_lessons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.category} | {self.title}"
```

### .\backend\apps\journal\api\serializers.py
```python
from rest_framework import serializers

from ..models import JournalEntry, Lesson, TradeNote


class TradeNoteSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = TradeNote
        fields = [
            "id",
            "symbol",
            "setup_description",
            "entry_reason",
            "exit_reason",
            "outcome",
            "pnl",
            "followed_plan",
            "mistake_type",
            "mistake_notes",
            "improvement",
            "screenshot_url",
            "created_at",
        ]


class TradeNoteCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradeNote
        fields = [
            "trade",
            "instrument",
            "setup_description",
            "entry_reason",
            "exit_reason",
            "outcome",
            "pnl",
            "followed_plan",
            "mistake_type",
            "mistake_notes",
            "improvement",
            "screenshot_url",
        ]


class JournalEntrySerializer(serializers.ModelSerializer):

    trade_notes = TradeNoteSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "date",
            "session",
            "title",
            "market_bias",
            "market_notes",
            "trades_taken",
            "winners",
            "losers",
            "total_pnl",
            "mood",
            "emotion_notes",
            "what_worked",
            "what_didnt_work",
            "lessons_learned",
            "tomorrow_plan",
            "ai_review",
            "ai_reviewed_at",
            "rating",
            "trade_notes",
            "created_at",
            "updated_at",
        ]


class JournalEntryCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalEntry
        fields = [
            "date",
            "session",
            "title",
            "market_bias",
            "market_notes",
            "trades_taken",
            "winners",
            "losers",
            "total_pnl",
            "mood",
            "emotion_notes",
            "what_worked",
            "what_didnt_work",
            "lessons_learned",
            "tomorrow_plan",
            "rating",
        ]


class LessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "content",
            "category",
            "is_rule",
            "times_reinforced",
            "created_at",
            "updated_at",
        ]


class LessonCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lesson
        fields = [
            "title",
            "content",
            "category",
            "is_rule",
        ]
```

### .\backend\apps\journal\api\urls.py
```python
from django.urls import path

from .views import (
    JournalAIReviewAPIView,
    JournalEntryDetailAPIView,
    JournalEntryListAPIView,
    JournalStatsAPIView,
    LessonListAPIView,
    LessonReinforceAPIView,
    MistakeListAPIView,
    RuleListAPIView,
    TradeNoteListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Journal Entries
    # ------------------------------------------------------------------
    path(
        "entries/",
        JournalEntryListAPIView.as_view(),
        name="journal-entries",
    ),
    path(
        "entries/<int:pk>/",
        JournalEntryDetailAPIView.as_view(),
        name="journal-entry-detail",
    ),
    path(
        "entries/<int:pk>/review/",
        JournalAIReviewAPIView.as_view(),
        name="journal-ai-review",
    ),
    path(
        "entries/<int:pk>/notes/",
        TradeNoteListAPIView.as_view(),
        name="journal-trade-notes",
    ),

    # ------------------------------------------------------------------
    # Stats & Analysis
    # ------------------------------------------------------------------
    path(
        "stats/",
        JournalStatsAPIView.as_view(),
        name="journal-stats",
    ),
    path(
        "mistakes/",
        MistakeListAPIView.as_view(),
        name="journal-mistakes",
    ),

    # ------------------------------------------------------------------
    # Lessons & Rules
    # ------------------------------------------------------------------
    path(
        "lessons/",
        LessonListAPIView.as_view(),
        name="journal-lessons",
    ),
    path(
        "lessons/<int:pk>/reinforce/",
        LessonReinforceAPIView.as_view(),
        name="journal-lesson-reinforce",
    ),
    path(
        "rules/",
        RuleListAPIView.as_view(),
        name="journal-rules",
    ),
]
```

### .\backend\apps\journal\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.ai_review_service import AIReviewService
from ..services.journal_service import JournalService
from .serializers import (
    JournalEntryCreateSerializer,
    JournalEntrySerializer,
    LessonCreateSerializer,
    LessonSerializer,
    TradeNoteCreateSerializer,
    TradeNoteSerializer,
)

logger = logging.getLogger(__name__)


class JournalEntryListAPIView(APIView):
    """
    GET  /api/journal/entries/     — list entries
    POST /api/journal/entries/     — create entry
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            date = request.query_params.get("date")
            limit = int(request.query_params.get("limit", 30))

            if date:
                entries = JournalService.get_by_date(request.user, date)
            else:
                entries = JournalService.get_entries(request.user, limit)

            serializer = JournalEntrySerializer(entries, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"JournalEntryListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch journal entries.")

    def post(self, request):
        serializer = JournalEntryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            entry = JournalService.create_entry(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=JournalEntrySerializer(entry).data,
                message="Journal entry created.",
            )
        except Exception as e:
            logger.error(f"JournalEntryListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create journal entry.")


class JournalEntryDetailAPIView(APIView):
    """
    GET    /api/journal/entries/<id>/  — get entry
    PUT    /api/journal/entries/<id>/  — update entry
    DELETE /api/journal/entries/<id>/  — delete entry
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")
        return ApiResponse.success(JournalEntrySerializer(entry).data)

    def put(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        serializer = JournalEntryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            updated = JournalService.update_entry(
                entry=entry,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=JournalEntrySerializer(updated).data,
                message="Journal entry updated.",
            )
        except Exception as e:
            logger.error(f"JournalEntryDetailAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update journal entry.")

    def delete(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        JournalService.delete_entry(entry)
        return ApiResponse.success(message="Journal entry deleted.")


class JournalAIReviewAPIView(APIView):
    """
    POST /api/journal/entries/<id>/review/
    Generate AI review for a journal entry.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        try:
            service = AIReviewService()
            review = service.review_entry(entry)
            return ApiResponse.success(
                data={"review": review},
                message="AI review generated.",
            )
        except Exception as e:
            logger.error(f"JournalAIReviewAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate AI review.")


class JournalStatsAPIView(APIView):
    """
    GET /api/journal/stats/
    Return journal statistics for the user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            stats = JournalService.get_stats(request.user)
            return ApiResponse.success(stats)
        except Exception as e:
            logger.error(f"JournalStatsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch stats.")


class TradeNoteListAPIView(APIView):
    """
    GET  /api/journal/entries/<id>/notes/  — list trade notes
    POST /api/journal/entries/<id>/notes/  — add trade note
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        notes = JournalService.get_trade_notes(entry)
        serializer = TradeNoteSerializer(notes, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request, pk: int):
        entry = JournalService.get_entry(request.user, pk)
        if not entry:
            return ApiResponse.error(message="Journal entry not found.")

        serializer = TradeNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            note = JournalService.add_trade_note(
                entry=entry,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=TradeNoteSerializer(note).data,
                message="Trade note added.",
            )
        except Exception as e:
            logger.error(f"TradeNoteListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to add trade note.")


class MistakeListAPIView(APIView):
    """
    GET /api/journal/mistakes/
    Return all trades with mistakes for pattern analysis.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mistakes = JournalService.get_mistakes(request.user)
            serializer = TradeNoteSerializer(mistakes, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"MistakeListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch mistakes.")


class LessonListAPIView(APIView):
    """
    GET  /api/journal/lessons/  — list lessons
    POST /api/journal/lessons/  — add lesson
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            category = request.query_params.get("category")
            lessons = JournalService.get_lessons(request.user, category)
            serializer = LessonSerializer(lessons, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"LessonListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch lessons.")

    def post(self, request):
        serializer = LessonCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            lesson = JournalService.add_lesson(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=LessonSerializer(lesson).data,
                message="Lesson added.",
            )
        except Exception as e:
            logger.error(f"LessonListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to add lesson.")


class RuleListAPIView(APIView):
    """
    GET /api/journal/rules/
    Return all hard trading rules.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rules = JournalService.get_rules(request.user)
            serializer = LessonSerializer(rules, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"RuleListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch rules.")


class LessonReinforceAPIView(APIView):
    """
    POST /api/journal/lessons/<id>/reinforce/
    Increment reinforcement count on a lesson.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            from ..repositories.journal_repository import LessonRepository
            lesson = LessonRepository.get_by_id(pk)

            if not lesson or lesson.user != request.user:
                return ApiResponse.error(message="Lesson not found.")

            lesson = JournalService.reinforce_lesson(lesson)
            return ApiResponse.success(
                data=LessonSerializer(lesson).data,
                message="Lesson reinforced.",
            )
        except Exception as e:
            logger.error(f"LessonReinforceAPIView error: {e}")
            return ApiResponse.error(message="Failed to reinforce lesson.")
```

### .\backend\apps\knowledge\admin.py
```python
from django.contrib import admin

from .models import Article, BookNote, Prompt, Tag, TradingRule


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "source",
        "is_featured",
        "view_count",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "source", "is_featured")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("ai_summary", "ai_summarized_at", "view_count")


@admin.register(BookNote)
class BookNoteAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "author",
        "rating",
        "started_at",
        "finished_at",
    )
    search_fields = ("title", "author")
    filter_horizontal = ("articles",)


@admin.register(TradingRule)
class TradingRuleAdmin(admin.ModelAdmin):

    list_display = (
        "rule_number",
        "title",
        "rule_type",
        "priority",
        "times_broken",
        "is_active",
    )
    list_filter = ("rule_type", "priority")
    search_fields = ("title", "description")


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "prompt_type",
        "use_count",
        "is_public",
        "created_at",
    )
    list_filter = ("prompt_type", "is_public")
    search_fields = ("title", "content")
```

### .\backend\apps\knowledge\apps.py
```python
from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge"
```

### .\backend\apps\knowledge\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from shared.models import BaseModel

User = get_user_model()


class Tag(BaseModel):
    """
    Tag for categorizing knowledge base content.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex color code for UI display.",
    )

    class Meta:
        db_table = "knowledge_tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Article(BaseModel):
    """
    A knowledge base article.
    Can be a trading concept, strategy note, market observation,
    or imported content from external sources.
    """

    CATEGORY_CHOICES = [
        ("CONCEPT", "Trading Concept"),
        ("STRATEGY", "Strategy"),
        ("INDICATOR", "Technical Indicator"),
        ("OPTION", "Options Theory"),
        ("PSYCHOLOGY", "Psychology"),
        ("RISK", "Risk Management"),
        ("MARKET", "Market Structure"),
        ("ZERODHA", "Zerodha Varsity"),
        ("BOOK", "Book Notes"),
        ("RESEARCH", "Research"),
        ("OTHER", "Other"),
    ]

    SOURCE_CHOICES = [
        ("MANUAL", "Manual Entry"),
        ("VARSITY", "Zerodha Varsity"),
        ("BOOK", "Book"),
        ("BLOG", "Blog/Article"),
        ("VIDEO", "Video"),
        ("AI", "AI Generated"),
        ("TRANSCRIPT", "Transcript"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )

    title = models.CharField(max_length=300, db_index=True)
    slug = models.SlugField(max_length=300, unique=True)
    category = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        default="CONCEPT",
        db_index=True,
    )
    source = models.CharField(
        max_length=15,
        choices=SOURCE_CHOICES,
        default="MANUAL",
    )
    source_url = models.URLField(blank=True)

    content = models.TextField()
    summary = models.TextField(
        blank=True,
        help_text="Short summary — AI generated or manual.",
    )
    key_points = models.JSONField(
        default=list,
        help_text="List of key takeaways.",
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles",
    )

    # AI Summary
    ai_summary = models.TextField(blank=True)
    ai_summarized_at = models.DateTimeField(null=True, blank=True)

    # Engagement
    view_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = "knowledge_articles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return self.title


class BookNote(BaseModel):
    """
    Notes from a trading book.
    Groups articles and highlights from a single book.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="book_notes",
    )

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=20, blank=True)

    summary = models.TextField(blank=True)
    key_lessons = models.JSONField(
        default=list,
        help_text="List of key lessons from the book.",
    )
    rating = models.IntegerField(
        default=0,
        help_text="Personal rating 1-10.",
    )

    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="books",
    )

    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "knowledge_book_notes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class TradingRule(BaseModel):
    """
    A hard trading rule extracted from experience or books.
    The personal rulebook — enforced by discipline.
    """

    RULE_TYPE_CHOICES = [
        ("ENTRY", "Entry Rule"),
        ("EXIT", "Exit Rule"),
        ("RISK", "Risk Rule"),
        ("PSYCHOLOGY", "Psychology Rule"),
        ("SYSTEM", "System Rule"),
    ]

    PRIORITY_CHOICES = [
        ("CRITICAL", "Critical — Never Break"),
        ("HIGH", "High — Rarely Break"),
        ("MEDIUM", "Medium — Use Judgment"),
        ("LOW", "Low — Guideline"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trading_rules",
    )

    rule_number = models.IntegerField(
        help_text="Rule number for ordering.",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(
        max_length=15,
        choices=RULE_TYPE_CHOICES,
        default="SYSTEM",
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="HIGH",
    )

    # How many times this rule was broken
    times_broken = models.IntegerField(default=0)
    last_broken_at = models.DateTimeField(null=True, blank=True)

    source_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rules",
    )

    class Meta:
        db_table = "knowledge_trading_rules"
        ordering = ["rule_number"]
        unique_together = [("user", "rule_number")]
        indexes = [
            models.Index(fields=["user", "rule_type"]),
            models.Index(fields=["user", "priority"]),
        ]

    def __str__(self) -> str:
        return f"Rule #{self.rule_number}: {self.title}"


class Prompt(BaseModel):
    """
    Stored AI prompts for the prompt library.
    Reusable prompts for analysis, research, and strategy development.
    """

    PROMPT_TYPE_CHOICES = [
        ("ANALYSIS", "Market Analysis"),
        ("RESEARCH", "Research"),
        ("STRATEGY", "Strategy Development"),
        ("REVIEW", "Trade Review"),
        ("LEARNING", "Learning"),
        ("CUSTOM", "Custom"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prompts",
    )

    title = models.CharField(max_length=200)
    prompt_type = models.CharField(
        max_length=15,
        choices=PROMPT_TYPE_CHOICES,
        default="CUSTOM",
        db_index=True,
    )
    content = models.TextField()
    description = models.TextField(blank=True)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
    )

    use_count = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "knowledge_prompts"
        ordering = ["-use_count", "-created_at"]

    def __str__(self) -> str:
        return self.title
```

### .\backend\apps\knowledge\api\serializers.py
```python
from rest_framework import serializers
from ..models import Article, BookNote, Prompt, Tag, TradingRule


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color"]


class ArticleListSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "source",
            "summary",
            "tags",
            "is_featured",
            "view_count",
            "created_at",
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "source",
            "source_url",
            "content",
            "summary",
            "key_points",
            "ai_summary",
            "ai_summarized_at",
            "tags",
            "is_featured",
            "view_count",
            "created_at",
            "updated_at",
        ]


class ArticleCreateSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = [
            "title",
            "slug",
            "category",
            "source",
            "source_url",
            "content",
            "summary",
            "key_points",
            "tags",
            "is_featured",
        ]


class BookNoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookNote
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "summary",
            "key_lessons",
            "rating",
            "started_at",
            "finished_at",
            "created_at",
        ]


class TradingRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradingRule
        fields = [
            "id",
            "rule_number",
            "title",
            "description",
            "rule_type",
            "priority",
            "times_broken",
            "last_broken_at",
            "is_active",
            "created_at",
        ]


class TradingRuleCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TradingRule
        fields = [
            "rule_number",
            "title",
            "description",
            "rule_type",
            "priority",
        ]


class PromptSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Prompt
        fields = [
            "id",
            "title",
            "prompt_type",
            "content",
            "description",
            "tags",
            "use_count",
            "is_public",
            "created_at",
        ]


class PromptCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prompt
        fields = [
            "title",
            "prompt_type",
            "content",
            "description",
            "is_public",
        ]
```

### .\backend\apps\knowledge\api\urls.py
```python
from django.urls import path

from .views import (
    ArticleDetailAPIView,
    ArticleListAPIView,
    ArticleSummarizeAPIView,
    BookNoteDetailAPIView,
    BookNoteListAPIView,
    KnowledgeSearchAPIView,
    PromptListAPIView,
    PromptUseAPIView,
    TagListAPIView,
    TradingRuleBrokenAPIView,
    TradingRuleDetailAPIView,
    TradingRuleListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    path(
        "search/",
        KnowledgeSearchAPIView.as_view(),
        name="knowledge-search",
    ),

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------
    path(
        "tags/",
        TagListAPIView.as_view(),
        name="knowledge-tags",
    ),

    # ------------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------------
    path(
        "articles/",
        ArticleListAPIView.as_view(),
        name="knowledge-articles",
    ),
    path(
        "articles/<slug:slug>/",
        ArticleDetailAPIView.as_view(),
        name="knowledge-article-detail",
    ),
    path(
        "articles/<slug:slug>/summarize/",
        ArticleSummarizeAPIView.as_view(),
        name="knowledge-article-summarize",
    ),

    # ------------------------------------------------------------------
    # Books
    # ------------------------------------------------------------------
    path(
        "books/",
        BookNoteListAPIView.as_view(),
        name="knowledge-books",
    ),
    path(
        "books/<int:pk>/",
        BookNoteDetailAPIView.as_view(),
        name="knowledge-book-detail",
    ),

    # ------------------------------------------------------------------
    # Trading Rules
    # ------------------------------------------------------------------
    path(
        "rules/",
        TradingRuleListAPIView.as_view(),
        name="knowledge-rules",
    ),
    path(
        "rules/<int:pk>/",
        TradingRuleDetailAPIView.as_view(),
        name="knowledge-rule-detail",
    ),
    path(
        "rules/<int:pk>/broken/",
        TradingRuleBrokenAPIView.as_view(),
        name="knowledge-rule-broken",
    ),

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    path(
        "prompts/",
        PromptListAPIView.as_view(),
        name="knowledge-prompts",
    ),
    path(
        "prompts/<int:pk>/use/",
        PromptUseAPIView.as_view(),
        name="knowledge-prompt-use",
    ),
]
```

### .\backend\apps\knowledge\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.ai_summary_service import AISummaryService
from ..services.knowledge_service import KnowledgeService
from ..services.search_service import SearchService
from .serializers import (
    ArticleCreateSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    BookNoteSerializer,
    PromptCreateSerializer,
    PromptSerializer,
    TagSerializer,
    TradingRuleCreateSerializer,
    TradingRuleSerializer,
)

logger = logging.getLogger(__name__)


class TagListAPIView(APIView):
    """GET /api/knowledge/tags/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tags = KnowledgeService.get_tags()
        serializer = TagSerializer(tags, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        try:
            tag = KnowledgeService.create_tag(request.data)
            return ApiResponse.success(
                data=TagSerializer(tag).data,
                message="Tag created.",
            )
        except Exception as e:
            return ApiResponse.error(message=str(e))


class ArticleListAPIView(APIView):
    """
    GET  /api/knowledge/articles/  — list articles
    POST /api/knowledge/articles/  — create article
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            category = request.query_params.get("category")
            tag = request.query_params.get("tag")
            featured = request.query_params.get("featured") == "1"
            limit = int(request.query_params.get("limit", 50))

            articles = KnowledgeService.get_articles(
                user=request.user,
                category=category,
                tag_slug=tag,
                featured=featured,
                limit=limit,
            )

            serializer = ArticleListSerializer(articles, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ArticleListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch articles.")

    def post(self, request):
        serializer = ArticleCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            article = KnowledgeService.create_article(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=ArticleDetailSerializer(article).data,
                message="Article created.",
            )
        except Exception as e:
            logger.error(f"ArticleListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create article.")


class ArticleDetailAPIView(APIView):
    """
    GET    /api/knowledge/articles/<slug>/
    PUT    /api/knowledge/articles/<slug>/
    DELETE /api/knowledge/articles/<slug>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article:
            return ApiResponse.error(message="Article not found.")
        return ApiResponse.success(ArticleDetailSerializer(article).data)

    def put(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article or article.user != request.user:
            return ApiResponse.error(message="Article not found.")

        serializer = ArticleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )

        try:
            updated = KnowledgeService.update_article(
                article=article,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=ArticleDetailSerializer(updated).data,
                message="Article updated.",
            )
        except Exception as e:
            logger.error(f"ArticleDetailAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update article.")

    def delete(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article or article.user != request.user:
            return ApiResponse.error(message="Article not found.")
        KnowledgeService.delete_article(article)
        return ApiResponse.success(message="Article deleted.")


class ArticleSummarizeAPIView(APIView):
    """
    POST /api/knowledge/articles/<slug>/summarize/
    Generate AI summary for an article.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, slug: str):
        article = KnowledgeService.get_article(slug)
        if not article:
            return ApiResponse.error(message="Article not found.")

        try:
            service = AISummaryService()
            result = service.summarize(article)
            return ApiResponse.success(
                data=result,
                message="AI summary generated.",
            )
        except Exception as e:
            logger.error(f"ArticleSummarizeAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate summary.")


class KnowledgeSearchAPIView(APIView):
    """
    GET /api/knowledge/search/?q=<query>
    Search across all knowledge base content.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return ApiResponse.error(message="Query parameter 'q' is required.")

        try:
            results = SearchService.search(request.user, query)
            return ApiResponse.success(results)
        except Exception as e:
            logger.error(f"KnowledgeSearchAPIView error: {e}")
            return ApiResponse.error(message="Search failed.")


class BookNoteListAPIView(APIView):
    """
    GET  /api/knowledge/books/
    POST /api/knowledge/books/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        books = KnowledgeService.get_books(request.user)
        serializer = BookNoteSerializer(books, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        serializer = BookNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            book = KnowledgeService.create_book(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=BookNoteSerializer(book).data,
                message="Book note created.",
            )
        except Exception as e:
            logger.error(f"BookNoteListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create book note.")


class BookNoteDetailAPIView(APIView):
    """
    GET /api/knowledge/books/<id>/
    PUT /api/knowledge/books/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        book = KnowledgeService.get_book(request.user, pk)
        if not book:
            return ApiResponse.error(message="Book note not found.")
        return ApiResponse.success(BookNoteSerializer(book).data)

    def put(self, request, pk: int):
        book = KnowledgeService.get_book(request.user, pk)
        if not book:
            return ApiResponse.error(message="Book note not found.")

        serializer = BookNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = KnowledgeService.update_book(book, serializer.validated_data)
        return ApiResponse.success(BookNoteSerializer(updated).data)


class TradingRuleListAPIView(APIView):
    """
    GET  /api/knowledge/rules/
    POST /api/knowledge/rules/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rule_type = request.query_params.get("type")
            critical = request.query_params.get("critical") == "1"

            if critical:
                rules = KnowledgeService.get_critical_rules(request.user)
            else:
                rules = KnowledgeService.get_rules(request.user, rule_type)

            serializer = TradingRuleSerializer(rules, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TradingRuleListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch rules.")

    def post(self, request):
        serializer = TradingRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            rule = KnowledgeService.create_rule(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=TradingRuleSerializer(rule).data,
                message="Trading rule created.",
            )
        except Exception as e:
            logger.error(f"TradingRuleListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create rule.")


class TradingRuleDetailAPIView(APIView):
    """
    PUT    /api/knowledge/rules/<id>/
    DELETE /api/knowledge/rules/<id>/
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk: int):
        from ..repositories.knowledge_repository import TradingRuleRepository
        rule = TradingRuleRepository.first(id=pk, user=request.user)
        if not rule:
            return ApiResponse.error(message="Rule not found.")

        serializer = TradingRuleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = KnowledgeService.update_rule(rule, serializer.validated_data)
        return ApiResponse.success(TradingRuleSerializer(updated).data)

    def delete(self, request, pk: int):
        from ..repositories.knowledge_repository import TradingRuleRepository
        rule = TradingRuleRepository.first(id=pk, user=request.user)
        if not rule:
            return ApiResponse.error(message="Rule not found.")
        KnowledgeService.delete_rule(rule)
        return ApiResponse.success(message="Rule deleted.")


class TradingRuleBrokenAPIView(APIView):
    """
    POST /api/knowledge/rules/<id>/broken/
    Record that a rule was broken.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            rule = KnowledgeService.record_rule_broken(pk, request.user)
            if not rule:
                return ApiResponse.error(message="Rule not found.")
            return ApiResponse.success(
                data=TradingRuleSerializer(rule).data,
                message="Rule breach recorded.",
            )
        except Exception as e:
            logger.error(f"TradingRuleBrokenAPIView error: {e}")
            return ApiResponse.error(message="Failed to record rule breach.")


class PromptListAPIView(APIView):
    """
    GET  /api/knowledge/prompts/
    POST /api/knowledge/prompts/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            prompt_type = request.query_params.get("type")
            public = request.query_params.get("public") == "1"

            if public:
                prompts = KnowledgeService.get_public_prompts()
            else:
                prompts = KnowledgeService.get_prompts(
                    request.user, prompt_type
                )

            serializer = PromptSerializer(prompts, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"PromptListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch prompts.")

    def post(self, request):
        serializer = PromptCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            prompt = KnowledgeService.create_prompt(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=PromptSerializer(prompt).data,
                message="Prompt created.",
            )
        except Exception as e:
            logger.error(f"PromptListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create prompt.")


class PromptUseAPIView(APIView):
    """
    POST /api/knowledge/prompts/<id>/use/
    Increment use count and return prompt content.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            prompt = KnowledgeService.use_prompt(pk, request.user)
            if not prompt:
                return ApiResponse.error(message="Prompt not found.")
            return ApiResponse.success(
                data=PromptSerializer(prompt).data,
                message="Prompt retrieved.",
            )
        except Exception as e:
            logger.error(f"PromptUseAPIView error: {e}")
            return ApiResponse.error(message="Failed to use prompt.")
```

### .\backend\apps\market_data\admin.py
```python
from django.contrib import admin

from .models import Candle, Instrument, Quote


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):

    list_display = (
        "symbol",
        "exchange",
        "instrument_token",
        "lot_size",
        "expiry",
    )

    search_fields = (
        "symbol",
        "trading_symbol",
    )

    list_filter = (
        "exchange",
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "last_price",
        "volume",
        "updated_at",
    )


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "timeframe",
        "candle_time",
        "close",
    )

    list_filter = (
        "timeframe",
    )
```

### .\backend\apps\market_data\apps.py
```python
from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.market_data"

```

### .\backend\apps\market_data\constants.py
```python
EXCHANGES = (
    "NSE",
    "BSE",
    "NFO",
    "MCX",
)

INDICES = (
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
    "SENSEX",
)
```

### .\backend\apps\market_data\models.py
```python
from django.db import models

from shared.models import BaseModel


class Instrument(BaseModel):
    """
    Represents a tradeable instrument — equity, index, future, or option.
    
    Key design decisions:
    - symbol: underlying name (NIFTY, BANKNIFTY, RELIANCE) — NOT unique
    - trading_symbol: Zerodha's unique identifier per contract — unique per exchange
    - instrument_token: Zerodha's numeric ID — globally unique
    """

    EXCHANGE_CHOICES = [
        ("NSE", "NSE"),
        ("BSE", "BSE"),
        ("NFO", "NFO"),
        ("MCX", "MCX"),
    ]

    OPTION_TYPE_CHOICES = [
        ("", "N/A"),
        ("CE", "CE"),
        ("PE", "PE"),
    ]

    INSTRUMENT_TYPE_CHOICES = [
        ("EQ", "Equity"),
        ("IDX", "Index"),
        ("FUT", "Future"),
        ("CE", "Call Option"),
        ("PE", "Put Option"),
    ]

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    instrument_token = models.BigIntegerField(
        unique=True,
        db_index=True,
        help_text="Zerodha's unique numeric token for this instrument.",
    )

    exchange_token = models.BigIntegerField(
        default=0,
        help_text="Exchange-level token.",
    )

    exchange = models.CharField(
        max_length=10,
        choices=EXCHANGE_CHOICES,
        db_index=True,
    )

    symbol = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Underlying symbol — e.g. NIFTY, RELIANCE. Not unique for derivatives.",
    )

    trading_symbol = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Zerodha trading symbol — unique per exchange e.g. NIFTY2572524000CE.",
    )

    instrument_type = models.CharField(
        max_length=10,
        choices=INSTRUMENT_TYPE_CHOICES,
        default="EQ",
        db_index=True,
    )

    # ------------------------------------------------------------------
    # Contract Details
    # ------------------------------------------------------------------

    lot_size = models.IntegerField(default=1)

    tick_size = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
    )

    # ------------------------------------------------------------------
    # Derivative Fields (null for equities/indices)
    # ------------------------------------------------------------------

    expiry = models.DateField(
        null=True,
        blank=True,
        db_index=True,
    )

    strike = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    option_type = models.CharField(
        max_length=2,
        choices=OPTION_TYPE_CHOICES,
        blank=True,
        default="",
        db_index=True,
    )

    class Meta:
        db_table = "market_instruments"
        ordering = ["symbol", "expiry", "strike"]
        # trading_symbol is unique within an exchange
        unique_together = [("exchange", "trading_symbol")]
        indexes = [
            models.Index(fields=["symbol", "exchange"]),
            models.Index(fields=["symbol", "expiry", "option_type"]),
            models.Index(fields=["instrument_token"]),
        ]

    def __str__(self) -> str:
        return self.trading_symbol

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_index(self) -> bool:
        """True if this is an index instrument."""
        return self.instrument_type == "IDX"

    @property
    def is_option(self) -> bool:
        """True if this is a CE or PE option."""
        return self.option_type in ("CE", "PE")

    @property
    def is_future(self) -> bool:
        """True if this is a futures contract."""
        return self.instrument_type == "FUT"

    @property
    def is_equity(self) -> bool:
        """True if this is an equity instrument."""
        return self.instrument_type == "EQ"


class Quote(BaseModel):
    """
    Real-time price snapshot for an instrument.
    Updated on every market tick from the live engine.
    One quote per instrument (OneToOne).
    """

    instrument = models.OneToOneField(
        Instrument,
        on_delete=models.CASCADE,
        related_name="quote",
    )

    last_price = models.DecimalField(max_digits=12, decimal_places=2)
    open_price = models.DecimalField(max_digits=12, decimal_places=2)
    high_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_price = models.DecimalField(max_digits=12, decimal_places=2)
    close_price = models.DecimalField(max_digits=12, decimal_places=2)

    change = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )

    volume = models.BigIntegerField(default=0)
    oi = models.BigIntegerField(default=0)

    bid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ask = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    bid_qty = models.BigIntegerField(default=0)
    ask_qty = models.BigIntegerField(default=0)

    class Meta:
        db_table = "market_quotes"

    def __str__(self) -> str:
        return f"{self.instrument.trading_symbol} @ {self.last_price}"


class Candle(BaseModel):
    """
    OHLCV candle for an instrument at a given timeframe.
    Used for technical analysis and backtesting.
    """

    TIMEFRAME_CHOICES = [
        ("1m", "1 Minute"),
        ("3m", "3 Minute"),
        ("5m", "5 Minute"),
        ("15m", "15 Minute"),
        ("30m", "30 Minute"),
        ("1h", "1 Hour"),
        ("1d", "1 Day"),
    ]

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="candles",
    )

    timeframe = models.CharField(
        max_length=10,
        choices=TIMEFRAME_CHOICES,
        db_index=True,
    )

    candle_time = models.DateTimeField(db_index=True)

    open = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    close = models.DecimalField(max_digits=12, decimal_places=2)

    volume = models.BigIntegerField(default=0)

    class Meta:
        db_table = "market_candles"
        ordering = ["-candle_time"]
        # Prevent duplicate candles for same instrument+timeframe+time
        unique_together = [("instrument", "timeframe", "candle_time")]
        indexes = [
            models.Index(fields=["instrument", "timeframe", "candle_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.instrument.trading_symbol} {self.timeframe} @ {self.candle_time}"
```

### .\backend\apps\market_data\utils.py
```python
from .constants import INDICES


def is_index(symbol):

    return symbol.upper() in INDICES
```

### .\backend\apps\market_data\api\serializers.py
```python
from rest_framework import serializers

from ..models import Candle, Instrument, Quote


class InstrumentSerializer(serializers.ModelSerializer):
    """Serializer for instrument list and search."""

    is_option = serializers.BooleanField(read_only=True)
    is_future = serializers.BooleanField(read_only=True)
    is_index = serializers.BooleanField(read_only=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "instrument_token",
            "exchange_token",
            "exchange",
            "symbol",
            "trading_symbol",
            "instrument_type",
            "lot_size",
            "tick_size",
            "expiry",
            "strike",
            "option_type",
            "is_option",
            "is_future",
            "is_index",
            "is_active",
            "created_at",
            "updated_at",
        ]


class QuoteSerializer(serializers.Serializer):
    """Serializer for live quote data from provider."""

    symbol = serializers.CharField()
    ltp = serializers.FloatField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    change = serializers.FloatField()
    change_percent = serializers.FloatField()
    volume = serializers.IntegerField()
    oi = serializers.IntegerField(default=0)
    bid = serializers.FloatField(default=0)
    ask = serializers.FloatField(default=0)
    timestamp = serializers.DateTimeField()


class CandleSerializer(serializers.ModelSerializer):
    """Serializer for OHLCV candle data."""

    class Meta:
        model = Candle
        fields = [
            "id",
            "timeframe",
            "candle_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]


class OptionChainSerializer(serializers.Serializer):
    """Serializer for a single option chain row."""

    strike = serializers.FloatField()
    option_type = serializers.CharField()
    ltp = serializers.FloatField()
    oi = serializers.IntegerField()
    volume = serializers.IntegerField()
    iv = serializers.FloatField(default=0)
    delta = serializers.FloatField(default=0)
    theta = serializers.FloatField(default=0)


class ExpirySerializer(serializers.Serializer):
    """Serializer for expiry date list."""

    expiry = serializers.DateField()


class BulkQuoteRequestSerializer(serializers.Serializer):
    """Serializer for validating bulk quote request body."""

    symbols = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=50,
    )
```

### .\backend\apps\market_data\api\urls.py
```python
from django.urls import path

from .views import (
    # Instruments
    BulkQuoteAPIView,
    ExpiryListAPIView,
    HistoricalDataAPIView,
    IndexListAPIView,
    InstrumentDetailAPIView,
    InstrumentListAPIView,
    InstrumentSearchAPIView,
    OptionChainAPIView,
    QuoteDetailAPIView,
    QuoteListAPIView,
    # Sprint 11 — Market Engine
    MarketEngineStatusAPIView,
    MarketSessionAPIView,
    # Sprint 12 — Indicators
    IndicatorAPIView,
    IndicatorListAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Instruments
    # ------------------------------------------------------------------
    path(
        "instruments/",
        InstrumentListAPIView.as_view(),
        name="instrument-list",
    ),
    path(
        "instruments/search/",
        InstrumentSearchAPIView.as_view(),
        name="instrument-search",
    ),
    path(
        "instruments/<str:symbol>/",
        InstrumentDetailAPIView.as_view(),
        name="instrument-detail",
    ),

    # ------------------------------------------------------------------
    # Indices
    # ------------------------------------------------------------------
    path(
        "indices/",
        IndexListAPIView.as_view(),
        name="index-list",
    ),

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------
    path(
        "quotes/",
        QuoteListAPIView.as_view(),
        name="quote-list",
    ),
    path(
        "quotes/bulk/",
        BulkQuoteAPIView.as_view(),
        name="quote-bulk",
    ),
    path(
        "quotes/<str:symbol>/",
        QuoteDetailAPIView.as_view(),
        name="quote-detail",
    ),

    # ------------------------------------------------------------------
    # Historical Data
    # ------------------------------------------------------------------
    path(
        "historical/<str:symbol>/",
        HistoricalDataAPIView.as_view(),
        name="historical-data",
    ),

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------
    path(
        "expiry/<str:symbol>/",
        ExpiryListAPIView.as_view(),
        name="expiry-list",
    ),

    # ------------------------------------------------------------------
    # Option Chain
    # ------------------------------------------------------------------
    path(
        "option-chain/<str:symbol>/",
        OptionChainAPIView.as_view(),
        name="option-chain",
    ),

    # ------------------------------------------------------------------
    # Sprint 11 — Market Engine
    # ------------------------------------------------------------------
    path(
        "session/",
        MarketSessionAPIView.as_view(),
        name="market-session",
    ),
    path(
        "engine/status/",
        MarketEngineStatusAPIView.as_view(),
        name="engine-status",
    ),

    # ------------------------------------------------------------------
    # Sprint 12 — Technical Indicators
    # ------------------------------------------------------------------
    path(
        "indicators/",
        IndicatorListAPIView.as_view(),
        name="indicator-list",
    ),
    path(
        "indicators/calculate/",
        IndicatorAPIView.as_view(),
        name="indicator-calculate",
    ),
]
```

### .\backend\apps\market_data\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..constants import INDICES
from ..services.candle_service import CandleService
from ..services.instrument_service import InstrumentService
from ..services.market_service import MarketService
from ..services.quote_service import QuoteService
from .serializers import (
    BulkQuoteRequestSerializer,
    CandleSerializer,
    ExpirySerializer,
    InstrumentSerializer,
    OptionChainSerializer,
    QuoteSerializer,
)

logger = logging.getLogger(__name__)


class InstrumentListAPIView(APIView):
    """
    GET /api/market/instruments/
    Return paginated list of all active instruments.
    Supports filtering by exchange and instrument_type.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        exchange = request.query_params.get("exchange")
        instrument_type = request.query_params.get("instrument_type")

        if exchange:
            instruments = InstrumentService.get_by_exchange(exchange.upper())
        elif instrument_type:
            from ..repositories.instrument_repository import InstrumentRepository
            instruments = InstrumentRepository.filter(
                instrument_type=instrument_type.upper(),
                is_active=True,
            )
        else:
            instruments = InstrumentService.get_all()

        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(
            data=serializer.data,
            message=f"{instruments.count()} instruments found.",
        )


class InstrumentSearchAPIView(APIView):
    """
    GET /api/market/instruments/search/?q=NIFTY
    Search instruments by symbol or trading symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query or len(query) < 2:
            return ApiResponse.error(
                message="Query parameter 'q' must be at least 2 characters.",
            )

        instruments = InstrumentService.search(query)
        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(
            data=serializer.data,
            message=f"{instruments.count()} instruments found.",
        )


class InstrumentDetailAPIView(APIView):
    """
    GET /api/market/instruments/<symbol>/
    Return a single instrument by symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        instrument = InstrumentService.get_by_symbol(symbol.upper())

        if not instrument:
            return ApiResponse.error(
                message=f"Instrument not found: {symbol}",
            )

        serializer = InstrumentSerializer(instrument)
        return ApiResponse.success(serializer.data)


class IndexListAPIView(APIView):
    """
    GET /api/market/indices/
    Return all index instruments.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        instruments = InstrumentService.get_indices()
        serializer = InstrumentSerializer(instruments, many=True)
        return ApiResponse.success(serializer.data)


class QuoteListAPIView(APIView):
    """
    GET /api/market/quotes/
    Return live quotes for all major indices.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = QuoteService()
            quotes = service.get_quotes(list(INDICES))
            serializer = QuoteSerializer(quotes, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"QuoteListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quotes.")


class QuoteDetailAPIView(APIView):
    """
    GET /api/market/quotes/<symbol>/
    Return live quote for a single symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = QuoteService()
            quote = service.get_quote(symbol.upper())

            if not quote:
                return ApiResponse.error(
                    message=f"Quote not found for: {symbol}",
                )

            serializer = QuoteSerializer(quote)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"QuoteDetailAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quote.")


class BulkQuoteAPIView(APIView):
    """
    POST /api/market/quotes/bulk/
    Return live quotes for a list of symbols.

    Request body:
        { "symbols": ["NIFTY", "BANKNIFTY", "RELIANCE"] }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BulkQuoteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            symbols = serializer.validated_data["symbols"]
            service = QuoteService()
            quotes = service.get_quotes([s.upper() for s in symbols])
            response_serializer = QuoteSerializer(quotes, many=True)
            return ApiResponse.success(response_serializer.data)
        except Exception as e:
            logger.error(f"BulkQuoteAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch quotes.")


class HistoricalDataAPIView(APIView):
    """
    GET /api/market/historical/<symbol>/
    Return historical OHLCV candles for a symbol.

    Query params:
        timeframe: 1m | 3m | 5m | 15m | 30m | 1h | 1d (default: 1d)
        limit: number of candles to return (default: 100)
    """

    permission_classes = [IsAuthenticated]

    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "1d"]

    def get(self, request, symbol: str):
        timeframe = request.query_params.get("timeframe", "1d").strip()
        limit = request.query_params.get("limit", 100)

        if timeframe not in self.VALID_TIMEFRAMES:
            return ApiResponse.error(
                message=f"Invalid timeframe. Choose from: {', '.join(self.VALID_TIMEFRAMES)}",
            )

        try:
            limit = int(limit)
            if limit < 1 or limit > 500:
                return ApiResponse.error(
                    message="Limit must be between 1 and 500.",
                )
        except ValueError:
            return ApiResponse.error(message="Invalid limit value.")

        try:
            candles = CandleService.get_candles(
                symbol=symbol.upper(),
                timeframe=timeframe,
                limit=limit,
            )
            serializer = CandleSerializer(candles, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"HistoricalDataAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch historical data.")


class ExpiryListAPIView(APIView):
    """
    GET /api/market/expiry/<symbol>/
    Return list of available expiry dates for a symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            from ..repositories.instrument_repository import InstrumentRepository

            expiries = (
                InstrumentRepository.filter(
                    symbol__iexact=symbol,
                    expiry__isnull=False,
                    is_active=True,
                )
                .values("expiry")
                .distinct()
                .order_by("expiry")
            )

            data = [{"expiry": e["expiry"]} for e in expiries]
            serializer = ExpirySerializer(data, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ExpiryListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch expiry dates.")


class OptionChainAPIView(APIView):
    """
    GET /api/market/option-chain/<symbol>/
    Return option chain for a given underlying symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        try:
            service = MarketService()
            chain = service.option_chain(symbol.upper())
            serializer = OptionChainSerializer(chain, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"OptionChainAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch option chain.")


# ----------------------------------------------------------------------
# Sprint 11 — Market Engine
# ----------------------------------------------------------------------

class MarketSessionAPIView(APIView):
    """
    GET /api/market/session/
    Return current market session state.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from ..engine.market_state import MarketState
            return ApiResponse.success(MarketState.session_info())
        except Exception as e:
            logger.error(f"MarketSessionAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch session info.")


class MarketEngineStatusAPIView(APIView):
    """
    GET /api/market/engine/status/
    Return current market engine status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from ..engine.market_state import MarketState
            from django.conf import settings

            provider = getattr(settings, "MARKET_PROVIDER", "mock")

            data = {
                "engine": "MarketEngine",
                "provider": provider,
                "session": MarketState.current_session(),
                "is_live": MarketState.is_live(),
                "websocket_endpoint": "ws://host/ws/market/quotes/",
            }

            return ApiResponse.success(data)
        except Exception as e:
            logger.error(f"MarketEngineStatusAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch engine status.")


# ----------------------------------------------------------------------
# Sprint 12 — Technical Indicators
# ----------------------------------------------------------------------

class IndicatorListAPIView(APIView):
    """
    GET /api/market/indicators/
    Return list of all supported indicators.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        indicators = {
            "moving_averages": [
                {"name": "SMA", "params": ["period"], "example": "SMA_20"},
                {"name": "EMA", "params": ["period"], "example": "EMA_9"},
                {"name": "WMA", "params": ["period"], "example": "WMA_20"},
            ],
            "momentum": [
                {"name": "RSI", "params": ["period"], "example": "RSI_14"},
                {"name": "MACD", "params": ["fast", "slow", "signal"], "example": "MACD_12_26_9"},
                {"name": "STOCH", "params": ["k_period", "d_period"], "example": "STOCH_14_3"},
            ],
            "volatility": [
                {"name": "BB", "params": ["period", "std_dev"], "example": "BB_20_2"},
                {"name": "ATR", "params": ["period"], "example": "ATR_14"},
            ],
            "volume": [
                {"name": "VWAP", "params": [], "example": "VWAP"},
                {"name": "OBV", "params": [], "example": "OBV"},
            ],
            "pivot": [
                {"name": "PIVOT", "params": [], "example": "PIVOT"},
                {"name": "CPR", "params": [], "example": "CPR"},
            ],
        }
        return ApiResponse.success(data=indicators)


class IndicatorAPIView(APIView):
    """
    POST /api/market/indicators/calculate/
    Calculate technical indicators for a symbol.

    Request body:
    {
        "symbol": "NIFTY",
        "timeframe": "15m",
        "indicators": ["EMA_9", "EMA_21", "RSI_14", "MACD", "BB_20"],
        "limit": 200
    }
    """

    permission_classes = [IsAuthenticated]

    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "1d"]

    def post(self, request):
        symbol = request.data.get("symbol", "").strip().upper()
        timeframe = request.data.get("timeframe", "1d").strip()
        indicators = request.data.get("indicators", [])
        limit = request.data.get("limit", 200)

        if not symbol:
            return ApiResponse.error(message="symbol is required.")

        if not indicators:
            return ApiResponse.error(message="indicators list is required.")

        if timeframe not in self.VALID_TIMEFRAMES:
            return ApiResponse.error(
                message=f"Invalid timeframe. Choose from: {', '.join(self.VALID_TIMEFRAMES)}"
            )

        try:
            limit = int(limit)
            limit = max(50, min(limit, 500))
        except (ValueError, TypeError):
            limit = 200

        try:
            from ..indicators.indicator_service import IndicatorService
            result = IndicatorService.calculate(
                symbol=symbol,
                timeframe=timeframe,
                indicators=indicators,
                limit=limit,
            )
            return ApiResponse.success(data=result)
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"IndicatorAPIView error: {e}")
            return ApiResponse.error(message="Failed to calculate indicators.")
```

### .\backend\apps\notifications\admin.py
```python
from django.contrib import admin

from .models import Alert, Notification, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "email_enabled",
        "telegram_enabled",
        "notify_ai_signals",
        "notify_strategy_signals",
        "notify_price_alerts",
    )
    search_fields = ("user__username",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "notification_type",
        "channel",
        "status",
        "title",
        "created_at",
    )
    list_filter = ("notification_type", "channel", "status")
    search_fields = ("user__username", "title")
    readonly_fields = ("sent_at", "read_at", "failed_reason")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "symbol",
        "alert_type",
        "target_value",
        "current_value",
        "status",
        "triggered_at",
    )
    list_filter = ("alert_type", "status")
    search_fields = ("user__username", "symbol")
```

### .\backend\apps\notifications\apps.py
```python
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
```

### .\backend\apps\notifications\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from shared.models import BaseModel

User = get_user_model()


class NotificationPreference(BaseModel):
    """
    User notification preferences.
    Controls which channels and events trigger notifications.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    # Channels
    email_enabled = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)

    # Telegram
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)

    # Email
    email_address = models.EmailField(blank=True)

    # Events
    notify_ai_signals = models.BooleanField(default=True)
    notify_strategy_signals = models.BooleanField(default=True)
    notify_price_alerts = models.BooleanField(default=True)
    notify_trade_execution = models.BooleanField(default=True)
    notify_market_open = models.BooleanField(default=False)
    notify_market_close = models.BooleanField(default=False)
    notify_daily_summary = models.BooleanField(default=True)

    # Quiet hours (IST)
    quiet_hours_enabled = models.BooleanField(default=True)
    quiet_from = models.TimeField(default="22:00")
    quiet_until = models.TimeField(default="08:00")

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"{self.user.username} — Notification Preferences"


class Notification(BaseModel):
    """
    A notification record.
    Tracks every notification sent to a user.
    """

    TYPE_CHOICES = [
        ("AI_SIGNAL", "AI Signal"),
        ("STRATEGY_SIGNAL", "Strategy Signal"),
        ("PRICE_ALERT", "Price Alert"),
        ("TRADE_EXECUTION", "Trade Execution"),
        ("MARKET_OPEN", "Market Open"),
        ("MARKET_CLOSE", "Market Close"),
        ("DAILY_SUMMARY", "Daily Summary"),
        ("SYSTEM", "System"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
    ]

    CHANNEL_CHOICES = [
        ("IN_APP", "In App"),
        ("EMAIL", "Email"),
        ("TELEGRAM", "Telegram"),
        ("PUSH", "Push"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("READ", "Read"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True,
    )
    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default="IN_APP",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(
        default=dict,
        help_text="Additional structured data for the notification.",
    )

    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} | {self.notification_type} | {self.status}"

    @property
    def is_read(self) -> bool:
        return self.status == "READ"


class Alert(BaseModel):
    """
    A price or signal alert set by the user.
    Triggers a notification when the condition is met.
    """

    ALERT_TYPE_CHOICES = [
        ("PRICE_ABOVE", "Price Above"),
        ("PRICE_BELOW", "Price Below"),
        ("PRICE_CROSS", "Price Crossover"),
        ("RSI_ABOVE", "RSI Above"),
        ("RSI_BELOW", "RSI Below"),
        ("VOLUME_SPIKE", "Volume Spike"),
        ("SIGNAL_BUY", "Buy Signal"),
        ("SIGNAL_SELL", "Sell Signal"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("TRIGGERED", "Triggered"),
        ("EXPIRED", "Expired"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="alerts",
    )

    symbol = models.CharField(max_length=50, db_index=True)
    alert_type = models.CharField(
        max_length=15,
        choices=ALERT_TYPE_CHOICES,
        db_index=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    # Condition
    target_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price or indicator value to trigger alert.",
    )
    current_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Last checked value.",
    )

    # Notification
    message = models.CharField(
        max_length=300,
        blank=True,
        help_text="Custom alert message.",
    )
    notify_email = models.BooleanField(default=True)
    notify_telegram = models.BooleanField(default=False)

    # Trigger info
    triggered_at = models.DateTimeField(null=True, blank=True)
    triggered_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Repeat
    repeat = models.BooleanField(
        default=False,
        help_text="Re-arm alert after triggering.",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["symbol", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.symbol} | {self.alert_type} @ "
            f"{self.target_value} [{self.status}]"
        )
```

### .\backend\apps\notifications\api\serializers.py
```python
from rest_framework import serializers

from ..models import Alert, Notification, NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "email_enabled",
            "telegram_enabled",
            "push_enabled",
            "telegram_chat_id",
            "telegram_username",
            "email_address",
            "notify_ai_signals",
            "notify_strategy_signals",
            "notify_price_alerts",
            "notify_trade_execution",
            "notify_market_open",
            "notify_market_close",
            "notify_daily_summary",
            "quiet_hours_enabled",
            "quiet_from",
            "quiet_until",
        ]


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "channel",
            "status",
            "title",
            "message",
            "data",
            "is_read",
            "read_at",
            "sent_at",
            "created_at",
        ]


class AlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alert
        fields = [
            "id",
            "symbol",
            "alert_type",
            "status",
            "target_value",
            "current_value",
            "message",
            "notify_email",
            "notify_telegram",
            "triggered_at",
            "triggered_value",
            "repeat",
            "expires_at",
            "created_at",
        ]


class AlertCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alert
        fields = [
            "symbol",
            "alert_type",
            "target_value",
            "message",
            "notify_email",
            "notify_telegram",
            "repeat",
            "expires_at",
        ]
```

### .\backend\apps\notifications\api\urls.py
```python
from django.urls import path

from .views import (
    AlertCancelAPIView,
    AlertCheckAPIView,
    AlertListAPIView,
    NotificationListAPIView,
    NotificationPreferenceAPIView,
    NotificationReadAllAPIView,
    NotificationReadAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),
    path(
        "<int:pk>/read/",
        NotificationReadAPIView.as_view(),
        name="notification-read",
    ),
    path(
        "read-all/",
        NotificationReadAllAPIView.as_view(),
        name="notification-read-all",
    ),
    path(
        "preferences/",
        NotificationPreferenceAPIView.as_view(),
        name="notification-preferences",
    ),

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    path(
        "alerts/",
        AlertListAPIView.as_view(),
        name="alert-list",
    ),
    path(
        "alerts/check/",
        AlertCheckAPIView.as_view(),
        name="alert-check",
    ),
    path(
        "alerts/<int:pk>/cancel/",
        AlertCancelAPIView.as_view(),
        name="alert-cancel",
    ),
]
```

### .\backend\apps\notifications\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.alert_service import AlertService
from ..services.notification_service import NotificationService
from .serializers import (
    AlertCreateSerializer,
    AlertSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)

logger = logging.getLogger(__name__)


class NotificationListAPIView(APIView):
    """
    GET /api/notifications/
    Return notifications for the user.

    Query params:
        unread=1  — unread only
        limit=50  — max results
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            unread_only = request.query_params.get("unread") == "1"
            limit = int(request.query_params.get("limit", 50))

            notifications = NotificationService.get_notifications(
                user=request.user,
                unread_only=unread_only,
                limit=limit,
            )
            unread_count = NotificationService.get_unread_count(request.user)

            serializer = NotificationSerializer(notifications, many=True)
            return ApiResponse.success(
                data={
                    "notifications": serializer.data,
                    "unread_count": unread_count,
                }
            )
        except Exception as e:
            logger.error(f"NotificationListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch notifications.")


class NotificationReadAPIView(APIView):
    """
    POST /api/notifications/<id>/read/
    Mark a notification as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        result = NotificationService.mark_read(pk, request.user)
        if result["success"]:
            return ApiResponse.success(message="Notification marked as read.")
        return ApiResponse.error(message=result["message"])


class NotificationReadAllAPIView(APIView):
    """
    POST /api/notifications/read-all/
    Mark all notifications as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_read(request.user)
        return ApiResponse.success(
            data={"marked_read": count},
            message=f"{count} notifications marked as read.",
        )


class NotificationPreferenceAPIView(APIView):
    """
    GET /api/notifications/preferences/
    PUT /api/notifications/preferences/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = NotificationService.get_preferences(request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return ApiResponse.success(serializer.data)

    def put(self, request):
        serializer = NotificationPreferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            prefs = NotificationService.update_preferences(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=NotificationPreferenceSerializer(prefs).data,
                message="Preferences updated.",
            )
        except Exception as e:
            logger.error(f"NotificationPreferenceAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update preferences.")


class AlertListAPIView(APIView):
    """
    GET  /api/notifications/alerts/  — list active alerts
    POST /api/notifications/alerts/  — create alert
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            alerts = AlertService.get_alerts(request.user)
            serializer = AlertSerializer(alerts, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"AlertListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch alerts.")

    def post(self, request):
        serializer = AlertCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            alert = AlertService.create_alert(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=AlertSerializer(alert).data,
                message="Alert created.",
            )
        except Exception as e:
            logger.error(f"AlertListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create alert.")


class AlertCancelAPIView(APIView):
    """
    POST /api/notifications/alerts/<id>/cancel/
    Cancel an active alert.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        result = AlertService.cancel_alert(request.user, pk)
        if result["success"]:
            return ApiResponse.success(message=result["message"])
        return ApiResponse.error(message=result["message"])


class AlertCheckAPIView(APIView):
    """
    POST /api/notifications/alerts/check/
    Manually trigger alert checking against current prices.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            service = AlertService()
            triggered = service.check_all_alerts()
            return ApiResponse.success(
                data={"triggered": triggered},
                message=f"{triggered} alerts triggered.",
            )
        except Exception as e:
            logger.error(f"AlertCheckAPIView error: {e}")
            return ApiResponse.error(message="Failed to check alerts.")
```

### .\backend\apps\paper_trading\admin.py
```python
from django.contrib import admin

from .models import PaperAccount, PaperOrder, PaperPosition, PaperTrade


@admin.register(PaperAccount)
class PaperAccountAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "balance",
        "total_pnl",
        "today_pnl",
        "total_trades",
        "winning_trades",
        "losing_trades",
    )


@admin.register(PaperOrder)
class PaperOrderAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "transaction_type",
        "order_type",
        "quantity",
        "price",
        "average_price",
        "status",
        "order_time",
    )

    list_filter = ("status", "transaction_type", "order_type")
    search_fields = ("instrument__symbol",)


@admin.register(PaperPosition)
class PaperPositionAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "direction",
        "quantity",
        "average_price",
        "last_price",
        "unrealized_pnl",
        "is_open",
    )

    list_filter = ("is_open", "direction")
    search_fields = ("instrument__symbol",)


@admin.register(PaperTrade)
class PaperTradeAdmin(admin.ModelAdmin):

    list_display = (
        "instrument",
        "direction",
        "quantity",
        "entry_price",
        "exit_price",
        "pnl",
        "net_pnl",
        "exit_time",
    )

    list_filter = ("direction", "product")
    search_fields = ("instrument__symbol",)
```

### .\backend\apps\paper_trading\apps.py
```python
from django.apps import AppConfig


class PaperTradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.paper_trading"
```

### .\backend\apps\paper_trading\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from apps.market_data.models import Instrument
from shared.models import BaseModel

User = get_user_model()


class PaperAccount(BaseModel):
    """
    Virtual trading account for paper trading.
    Each user has one paper account.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="paper_account",
    )

    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=1000000.00,
        help_text="Available cash balance.",
    )
    initial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=1000000.00,
    )
    used_margin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    total_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Cumulative realized PnL.",
    )
    today_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)

    class Meta:
        db_table = "paper_accounts"

    def __str__(self) -> str:
        return f"{self.user.username} — ₹{self.balance}"

    @property
    def win_rate(self) -> float:
        """Return win rate as percentage."""
        if self.total_trades == 0:
            return 0.0
        return round(self.winning_trades / self.total_trades * 100, 2)

    @property
    def available_balance(self) -> float:
        """Return available balance after margin."""
        return float(self.balance) - float(self.used_margin)

    @property
    def total_return_pct(self) -> float:
        """Return total return as percentage."""
        if self.initial_balance == 0:
            return 0.0
        return round(
            float(self.total_pnl) / float(self.initial_balance) * 100, 2
        )


class PaperOrder(BaseModel):
    """
    A paper trading order.
    Mimics a real broker order without actual execution.
    """

    ORDER_TYPE_CHOICES = [
        ("MARKET", "Market"),
        ("LIMIT", "Limit"),
        ("SL", "Stop Loss"),
        ("SL_M", "Stop Loss Market"),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("OPEN", "Open"),
        ("COMPLETE", "Complete"),
        ("CANCELLED", "Cancelled"),
        ("REJECTED", "Rejected"),
    ]

    PRODUCT_CHOICES = [
        ("MIS", "Intraday (MIS)"),
        ("NRML", "Normal (NRML)"),
        ("CNC", "Delivery (CNC)"),
    ]

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_orders",
    )

    order_type = models.CharField(
        max_length=10,
        choices=ORDER_TYPE_CHOICES,
        default="MARKET",
    )
    transaction_type = models.CharField(
        max_length=5,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True,
    )
    product = models.CharField(
        max_length=5,
        choices=PRODUCT_CHOICES,
        default="MIS",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Limit price. 0 for market orders.",
    )
    trigger_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Trigger price for SL orders.",
    )
    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Actual execution price.",
    )

    filled_quantity = models.IntegerField(default=0)
    pending_quantity = models.IntegerField(default=0)

    order_time = models.DateTimeField(auto_now_add=True, db_index=True)
    execution_time = models.DateTimeField(null=True, blank=True)

    # Source of the order
    tag = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tag to identify order source e.g. strategy name.",
    )
    notes = models.TextField(blank=True)
    reject_reason = models.TextField(blank=True)

    class Meta:
        db_table = "paper_orders"
        ordering = ["-order_time"]
        indexes = [
            models.Index(fields=["account", "status"]),
            models.Index(fields=["account", "order_time"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.transaction_type} {self.quantity} "
            f"{self.instrument.symbol} @ {self.price} [{self.status}]"
        )


class PaperPosition(BaseModel):
    """
    An open paper trading position.
    Created when an order is executed, updated on partial fills.
    """

    DIRECTION_CHOICES = [
        ("LONG", "Long"),
        ("SHORT", "Short"),
    ]

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="positions",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_positions",
    )

    direction = models.CharField(
        max_length=5,
        choices=DIRECTION_CHOICES,
    )
    quantity = models.IntegerField()
    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    last_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    unrealized_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    realized_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True, db_index=True)

    product = models.CharField(max_length=5, default="MIS")
    tag = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "paper_positions"
        ordering = ["-open_time"]
        indexes = [
            models.Index(fields=["account", "is_open"]),
            models.Index(fields=["account", "instrument"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.direction} {self.quantity} "
            f"{self.instrument.symbol} @ {self.average_price}"
        )

    @property
    def current_value(self) -> float:
        """Current market value of the position."""
        return float(self.quantity) * float(self.last_price)

    @property
    def invested_value(self) -> float:
        """Original invested value."""
        return float(self.quantity) * float(self.average_price)

    @property
    def pnl_pct(self) -> float:
        """PnL as percentage of invested value."""
        if self.invested_value == 0:
            return 0.0
        return round(
            float(self.unrealized_pnl) / self.invested_value * 100, 2
        )


class PaperTrade(BaseModel):
    """
    A completed paper trade — records the full lifecycle.
    Created when a position is closed.
    Used for journaling and backtesting.
    """

    account = models.ForeignKey(
        PaperAccount,
        on_delete=models.CASCADE,
        related_name="trades",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="paper_trades",
    )
    position = models.OneToOneField(
        PaperPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trade",
    )

    direction = models.CharField(max_length=5)
    quantity = models.IntegerField()

    entry_price = models.DecimalField(max_digits=12, decimal_places=2)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2)

    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField()

    pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Realized PnL for this trade.",
    )
    pnl_pct = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0,
    )

    brokerage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )
    net_pnl = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="PnL after brokerage.",
    )

    product = models.CharField(max_length=5, default="MIS")
    tag = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    # Source signals
    strategy_signal = models.CharField(max_length=50, blank=True)
    ai_signal = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "paper_trades"
        ordering = ["-exit_time"]
        indexes = [
            models.Index(fields=["account", "exit_time"]),
            models.Index(fields=["instrument", "exit_time"]),
        ]

    def __str__(self) -> str:
        result = "WIN" if float(self.pnl) > 0 else "LOSS"
        return (
            f"{result} | {self.direction} {self.quantity} "
            f"{self.instrument.symbol} | ₹{self.pnl}"
        )
```

### .\backend\apps\paper_trading\api\serializers.py
```python
from rest_framework import serializers

from ..models import PaperAccount, PaperOrder, PaperPosition, PaperTrade


class PaperAccountSerializer(serializers.ModelSerializer):

    win_rate = serializers.FloatField(read_only=True)
    available_balance = serializers.FloatField(read_only=True)
    total_return_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = PaperAccount
        fields = [
            "id",
            "balance",
            "initial_balance",
            "used_margin",
            "available_balance",
            "total_pnl",
            "today_pnl",
            "total_return_pct",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
        ]


class PaperOrderSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = PaperOrder
        fields = [
            "id",
            "symbol",
            "transaction_type",
            "order_type",
            "product",
            "status",
            "quantity",
            "price",
            "average_price",
            "filled_quantity",
            "pending_quantity",
            "order_time",
            "execution_time",
            "tag",
            "notes",
            "reject_reason",
        ]


class PlaceOrderSerializer(serializers.Serializer):
    """Request body for placing a paper order."""
    symbol = serializers.CharField()
    transaction_type = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(
        choices=["MARKET", "LIMIT"],
        default="MARKET",
    )
    price = serializers.FloatField(default=0)
    product = serializers.ChoiceField(
        choices=["MIS", "NRML", "CNC"],
        default="MIS",
    )
    tag = serializers.CharField(default="", allow_blank=True)


class PaperPositionSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    trading_symbol = serializers.CharField(
        source="instrument.trading_symbol",
        read_only=True,
    )
    current_value = serializers.FloatField(read_only=True)
    invested_value = serializers.FloatField(read_only=True)
    pnl_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = PaperPosition
        fields = [
            "id",
            "symbol",
            "trading_symbol",
            "direction",
            "quantity",
            "average_price",
            "last_price",
            "current_value",
            "invested_value",
            "unrealized_pnl",
            "realized_pnl",
            "pnl_pct",
            "product",
            "tag",
            "open_time",
            "is_open",
        ]


class PaperTradeSerializer(serializers.ModelSerializer):

    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )

    class Meta:
        model = PaperTrade
        fields = [
            "id",
            "symbol",
            "direction",
            "quantity",
            "entry_price",
            "exit_price",
            "entry_time",
            "exit_time",
            "pnl",
            "pnl_pct",
            "brokerage",
            "net_pnl",
            "product",
            "tag",
            "strategy_signal",
            "ai_signal",
        ]
```

### .\backend\apps\paper_trading\api\urls.py
```python
from django.urls import path

from .views import (
    OrderCancelAPIView,
    OrderListAPIView,
    PortfolioAPIView,
    PortfolioResetAPIView,
    PositionListAPIView,
    TodayOrdersAPIView,
    TodayTradesAPIView,
    TradeHistoryAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------
    path(
        "portfolio/",
        PortfolioAPIView.as_view(),
        name="paper-portfolio",
    ),
    path(
        "portfolio/reset/",
        PortfolioResetAPIView.as_view(),
        name="paper-portfolio-reset",
    ),

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    path(
        "orders/",
        OrderListAPIView.as_view(),
        name="paper-orders",
    ),
    path(
        "orders/today/",
        TodayOrdersAPIView.as_view(),
        name="paper-orders-today",
    ),
    path(
        "orders/<int:pk>/cancel/",
        OrderCancelAPIView.as_view(),
        name="paper-order-cancel",
    ),

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------
    path(
        "positions/",
        PositionListAPIView.as_view(),
        name="paper-positions",
    ),

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------
    path(
        "trades/",
        TradeHistoryAPIView.as_view(),
        name="paper-trades",
    ),
    path(
        "trades/today/",
        TodayTradesAPIView.as_view(),
        name="paper-trades-today",
    ),
]
```

### .\backend\apps\paper_trading\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.order_service import OrderService
from ..services.portfolio_service import PortfolioService
from ..services.position_service import PositionService
from .serializers import (
    PaperOrderSerializer,
    PaperPositionSerializer,
    PaperTradeSerializer,
    PlaceOrderSerializer,
)

logger = logging.getLogger(__name__)


class PortfolioAPIView(APIView):
    """
    GET /api/paper/portfolio/
    Return full portfolio summary.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = PortfolioService.get_portfolio(request.user)
            return ApiResponse.success(data)
        except Exception as e:
            logger.error(f"PortfolioAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch portfolio.")


class PortfolioResetAPIView(APIView):
    """
    POST /api/paper/portfolio/reset/
    Reset paper trading account to initial state.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            result = PortfolioService.reset_account(request.user)
            return ApiResponse.success(data=result)
        except Exception as e:
            logger.error(f"PortfolioResetAPIView error: {e}")
            return ApiResponse.error(message="Failed to reset account.")


class OrderListAPIView(APIView):
    """
    GET  /api/paper/orders/        — list orders
    POST /api/paper/orders/        — place order
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            status = request.query_params.get("status")
            service = OrderService()
            orders = service.get_orders(request.user, status)
            serializer = PaperOrderSerializer(orders, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"OrderListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch orders.")

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )

        try:
            service = OrderService()
            result = service.place_order(
                user=request.user,
                symbol=serializer.validated_data["symbol"].upper(),
                transaction_type=serializer.validated_data["transaction_type"],
                quantity=serializer.validated_data["quantity"],
                order_type=serializer.validated_data["order_type"],
                price=serializer.validated_data["price"],
                product=serializer.validated_data["product"],
                tag=serializer.validated_data["tag"],
            )

            if result["success"]:
                return ApiResponse.success(
                    data=result,
                    message="Order placed successfully.",
                )
            return ApiResponse.error(message=result["message"])

        except Exception as e:
            logger.error(f"OrderListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to place order.")


class OrderCancelAPIView(APIView):
    """
    POST /api/paper/orders/<id>/cancel/
    Cancel a pending order.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        try:
            service = OrderService()
            result = service.cancel_order(request.user, pk)

            if result["success"]:
                return ApiResponse.success(data=result)
            return ApiResponse.error(message=result["message"])

        except Exception as e:
            logger.error(f"OrderCancelAPIView error: {e}")
            return ApiResponse.error(message="Failed to cancel order.")


class TodayOrdersAPIView(APIView):
    """
    GET /api/paper/orders/today/
    Return today's orders.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = OrderService()
            orders = service.get_today_orders(request.user)
            serializer = PaperOrderSerializer(orders, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TodayOrdersAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch today's orders.")


class PositionListAPIView(APIView):
    """
    GET /api/paper/positions/
    Return all open positions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            positions = PositionService.get_open_positions(request.user)
            serializer = PaperPositionSerializer(positions, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"PositionListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch positions.")


class TradeHistoryAPIView(APIView):
    """
    GET /api/paper/trades/
    Return completed trade history.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 50))
            trades = PortfolioService.get_trade_history(request.user, limit)
            serializer = PaperTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TradeHistoryAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch trade history.")


class TodayTradesAPIView(APIView):
    """
    GET /api/paper/trades/today/
    Return today's completed trades.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trades = PortfolioService.get_today_trades(request.user)
            serializer = PaperTradeSerializer(trades, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"TodayTradesAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch today's trades.")
```

### .\backend\apps\strategies\admin.py
```python
from django.contrib import admin

from .models import Strategy, StrategySignal


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "strategy_type",
        "timeframe",
        "is_enabled",
        "is_active",
        "created_at",
    )

    list_filter = (
        "strategy_type",
        "timeframe",
        "is_enabled",
    )

    search_fields = ("name",)


@admin.register(StrategySignal)
class StrategySignalAdmin(admin.ModelAdmin):

    list_display = (
        "strategy",
        "instrument",
        "signal",
        "strength",
        "status",
        "price_at_signal",
        "signal_time",
    )

    list_filter = (
        "signal",
        "strength",
        "status",
        "timeframe",
    )

    search_fields = (
        "instrument__symbol",
        "strategy__name",
    )
```

### .\backend\apps\strategies\apps.py
```python
from django.apps import AppConfig


class StrategiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.strategies"
```

### .\backend\apps\strategies\models.py
```python
from django.db import models

from apps.market_data.models import Instrument
from shared.models import BaseModel


class Strategy(BaseModel):
    """
    Defines a trading strategy configuration.
    Each strategy has rules, parameters, and generates signals.
    """

    STRATEGY_TYPE_CHOICES = [
        ("EMA_CROSSOVER", "EMA Crossover"),
        ("RSI", "RSI Overbought/Oversold"),
        ("VWAP", "VWAP Reversal"),
        ("ORB", "Opening Range Breakout"),
        ("MACD", "MACD Crossover"),
        ("BOLLINGER", "Bollinger Band Squeeze"),
        ("CUSTOM", "Custom Strategy"),
    ]

    TIMEFRAME_CHOICES = [
        ("1m", "1 Minute"),
        ("3m", "3 Minute"),
        ("5m", "5 Minute"),
        ("15m", "15 Minute"),
        ("30m", "30 Minute"),
        ("1h", "1 Hour"),
        ("1d", "1 Day"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    strategy_type = models.CharField(
        max_length=20,
        choices=STRATEGY_TYPE_CHOICES,
        db_index=True,
    )
    timeframe = models.CharField(
        max_length=10,
        choices=TIMEFRAME_CHOICES,
        default="15m",
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Strategy-specific parameters as JSON.",
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "strategies"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.strategy_type})"


class StrategySignal(BaseModel):
    """
    A trading signal generated by a strategy.
    Records the signal type, price, and context at time of generation.
    """

    SIGNAL_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
        ("NEUTRAL", "Neutral"),
    ]

    STRENGTH_CHOICES = [
        ("STRONG", "Strong"),
        ("MODERATE", "Moderate"),
        ("WEAK", "Weak"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("TRIGGERED", "Triggered"),
    ]

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="signals",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="signals",
    )

    signal = models.CharField(
        max_length=10,
        choices=SIGNAL_CHOICES,
        db_index=True,
    )
    strength = models.CharField(
        max_length=10,
        choices=STRENGTH_CHOICES,
        default="MODERATE",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    price_at_signal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    target_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stop_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    timeframe = models.CharField(max_length=10)
    signal_time = models.DateTimeField(db_index=True)

    # Context snapshot at time of signal
    context = models.JSONField(
        default=dict,
        help_text="Indicator values and market context at signal time.",
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "strategy_signals"
        ordering = ["-signal_time"]
        indexes = [
            models.Index(fields=["instrument", "signal_time"]),
            models.Index(fields=["strategy", "signal_time"]),
            models.Index(fields=["signal", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.strategy.name} | "
            f"{self.instrument.symbol} | "
            f"{self.signal} @ {self.price_at_signal}"
        )
```

### .\backend\apps\strategies\api\serializers.py
```python
from rest_framework import serializers

from ..models import Strategy, StrategySignal


class StrategySerializer(serializers.ModelSerializer):

    class Meta:
        model = Strategy
        fields = [
            "id",
            "name",
            "description",
            "strategy_type",
            "timeframe",
            "parameters",
            "is_enabled",
            "is_active",
            "created_at",
            "updated_at",
        ]


class StrategyCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Strategy
        fields = [
            "name",
            "description",
            "strategy_type",
            "timeframe",
            "parameters",
            "is_enabled",
        ]


class StrategySignalSerializer(serializers.ModelSerializer):

    strategy_name = serializers.CharField(
        source="strategy.name",
        read_only=True,
    )
    symbol = serializers.CharField(
        source="instrument.symbol",
        read_only=True,
    )
    trading_symbol = serializers.CharField(
        source="instrument.trading_symbol",
        read_only=True,
    )

    class Meta:
        model = StrategySignal
        fields = [
            "id",
            "strategy_name",
            "symbol",
            "trading_symbol",
            "signal",
            "strength",
            "status",
            "price_at_signal",
            "target_price",
            "stop_loss",
            "timeframe",
            "signal_time",
            "context",
            "notes",
            "created_at",
        ]


class RunStrategySerializer(serializers.Serializer):
    """Request body for running a strategy."""
    symbol = serializers.CharField()
    strategy_id = serializers.IntegerField()


class RunAllSerializer(serializers.Serializer):
    """Request body for running all strategies."""
    symbols = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=20,
    )
```

### .\backend\apps\strategies\api\urls.py
```python
from django.urls import path

from .views import (
    SignalBySymbolAPIView,
    SignalListAPIView,
    StrategyDetailAPIView,
    StrategyListAPIView,
    StrategyRunAllAPIView,
    StrategyRunAPIView,
)

urlpatterns = [
    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------
    path(
        "",
        StrategyListAPIView.as_view(),
        name="strategy-list",
    ),
    path(
        "<int:pk>/",
        StrategyDetailAPIView.as_view(),
        name="strategy-detail",
    ),
    path(
        "run/",
        StrategyRunAPIView.as_view(),
        name="strategy-run",
    ),
    path(
        "run-all/",
        StrategyRunAllAPIView.as_view(),
        name="strategy-run-all",
    ),

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    path(
        "signals/",
        SignalListAPIView.as_view(),
        name="signal-list",
    ),
    path(
        "signals/<str:symbol>/",
        SignalBySymbolAPIView.as_view(),
        name="signal-by-symbol",
    ),
]
```

### .\backend\apps\strategies\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.strategy_service import StrategyService
from .serializers import (
    RunAllSerializer,
    RunStrategySerializer,
    StrategyCreateSerializer,
    StrategySerializer,
    StrategySignalSerializer,
)

logger = logging.getLogger(__name__)


class StrategyListAPIView(APIView):
    """
    GET  /api/strategies/          — list all strategies
    POST /api/strategies/          — create a strategy
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        strategies = StrategyService.get_all()
        serializer = StrategySerializer(strategies, many=True)
        return ApiResponse.success(serializer.data)

    def post(self, request):
        serializer = StrategyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        strategy = StrategyService.create(serializer.validated_data)
        return ApiResponse.success(
            data=StrategySerializer(strategy).data,
            message="Strategy created.",
        )


class StrategyDetailAPIView(APIView):
    """
    GET    /api/strategies/<id>/   — get strategy
    PUT    /api/strategies/<id>/   — update strategy
    DELETE /api/strategies/<id>/   — delete strategy
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")
        return ApiResponse.success(StrategySerializer(strategy).data)

    def put(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")

        serializer = StrategyCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        updated = StrategyService.update(strategy, serializer.validated_data)
        return ApiResponse.success(
            data=StrategySerializer(updated).data,
            message="Strategy updated.",
        )

    def delete(self, request, pk: int):
        strategy = StrategyService.get_by_id(pk)
        if not strategy:
            return ApiResponse.error(message="Strategy not found.")
        StrategyService.delete(strategy)
        return ApiResponse.success(message="Strategy deleted.")


class StrategyRunAPIView(APIView):
    """
    POST /api/strategies/run/
    Run a single strategy against a symbol.

    Request body:
        { "strategy_id": 1, "symbol": "NIFTY" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunStrategySerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )
        try:
            result = StrategyService.run_strategy(
                strategy_id=serializer.validated_data["strategy_id"],
                symbol=serializer.validated_data["symbol"].upper(),
            )
            if not result:
                return ApiResponse.error(
                    message="Strategy returned no signal. Check candle data.",
                )
            return ApiResponse.success(data=result)
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"StrategyRunAPIView error: {e}")
            return ApiResponse.error(message="Strategy execution failed.")


class StrategyRunAllAPIView(APIView):
    """
    POST /api/strategies/run-all/
    Run all enabled strategies against a list of symbols.

    Request body:
        { "symbols": ["NIFTY", "BANKNIFTY"] }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunAllSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid request.",
                errors=serializer.errors,
            )
        try:
            symbols = [s.upper() for s in serializer.validated_data["symbols"]]
            results = StrategyService.run_all(symbols)
            return ApiResponse.success(data=results)
        except Exception as e:
            logger.error(f"StrategyRunAllAPIView error: {e}")
            return ApiResponse.error(message="Strategy execution failed.")


class SignalListAPIView(APIView):
    """
    GET /api/strategies/signals/          — today's signals
    GET /api/strategies/signals/?active=1 — active signals only
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get("active") == "1"

        if active_only:
            signals = StrategyService.get_active_signals()
        else:
            signals = StrategyService.get_today_signals()

        serializer = StrategySignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)


class SignalBySymbolAPIView(APIView):
    """
    GET /api/strategies/signals/<symbol>/
    Return recent signals for a symbol.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol: str):
        signals = StrategyService.get_signals_for_instrument(symbol.upper())
        serializer = StrategySignalSerializer(signals, many=True)
        return ApiResponse.success(serializer.data)
```

### .\backend\apps\zerodha\admin.py
```python
from django.contrib import admin

from .models import ZerodhaConfig, ZerodhaSession


@admin.register(ZerodhaConfig)
class ZerodhaConfigAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "is_connected",
        "connected_at",
        "token_expires_at",
        "mcp_url",
    )
    readonly_fields = (
        "access_token",
        "request_token",
        "is_connected",
        "connected_at",
        "token_expires_at",
    )
    search_fields = ("user__username",)


@admin.register(ZerodhaSession)
class ZerodhaSessionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "zerodha_user_id",
        "zerodha_username",
        "status",
        "login_at",
        "expires_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "access_token",
        "login_at",
    )
```

### .\backend\apps\zerodha\apps.py
```python
from django.apps import AppConfig


class ZerodhaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.zerodha"
```

### .\backend\apps\zerodha\models.py
```python
from django.db import models
from django.contrib.auth import get_user_model

from shared.models import BaseModel

User = get_user_model()


class ZerodhaConfig(BaseModel):
    """
    Zerodha API configuration per user.
    Stores API key and access token for Kite Connect.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="zerodha_config",
    )

    api_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Zerodha Kite Connect API key.",
    )
    api_secret = models.CharField(
        max_length=100,
        blank=True,
        help_text="Zerodha Kite Connect API secret.",
    )
    access_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Current active access token.",
    )
    request_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Request token from login redirect.",
    )

    is_connected = models.BooleanField(default=False)
    connected_at = models.DateTimeField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # MCP endpoint
    mcp_url = models.URLField(
        default="https://mcp.kite.trade/mcp",
        help_text="Zerodha MCP server URL.",
    )

    class Meta:
        db_table = "zerodha_configs"

    def __str__(self) -> str:
        return f"{self.user.username} — Zerodha Config"

    @property
    def is_token_valid(self) -> bool:
        """Check if access token is still valid."""
        if not self.access_token or not self.is_connected:
            return False
        if not self.token_expires_at:
            return True
        from django.utils import timezone
        return timezone.now() < self.token_expires_at


class ZerodhaSession(BaseModel):
    """
    Tracks Zerodha login sessions.
    Records each authentication event.
    """

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("REVOKED", "Revoked"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="zerodha_sessions",
    )
    config = models.ForeignKey(
        ZerodhaConfig,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    access_token = models.CharField(max_length=500)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        db_index=True,
    )

    login_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Profile snapshot at login
    zerodha_user_id = models.CharField(max_length=20, blank=True)
    zerodha_username = models.CharField(max_length=100, blank=True)
    broker = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    user_type = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "zerodha_sessions"
        ordering = ["-login_at"]

    def __str__(self) -> str:
        return (
            f"{self.user.username} | "
            f"{self.zerodha_user_id} | "
            f"{self.status}"
        )
```

### .\backend\apps\zerodha\api\serializers.py
```python
from rest_framework import serializers

from ..models import ZerodhaConfig, ZerodhaSession


class ZerodhaConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = ZerodhaConfig
        fields = [
            "id",
            "api_key",
            "is_connected",
            "connected_at",
            "token_expires_at",
            "mcp_url",
            "is_token_valid",
        ]
        read_only_fields = [
            "is_connected",
            "connected_at",
            "token_expires_at",
            "is_token_valid",
        ]


class ZerodhaConfigUpdateSerializer(serializers.Serializer):
    """Request body for saving Zerodha config."""
    api_key = serializers.CharField()
    api_secret = serializers.CharField()
    mcp_url = serializers.URLField(
        default="https://mcp.kite.trade/mcp",
    )


class TokenExchangeSerializer(serializers.Serializer):
    """Request body for token exchange."""
    request_token = serializers.CharField()


class ZerodhaSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ZerodhaSession
        fields = [
            "id",
            "zerodha_user_id",
            "zerodha_username",
            "broker",
            "email",
            "user_type",
            "status",
            "login_at",
            "expires_at",
        ]


class OrderPlaceSerializer(serializers.Serializer):
    """Request body for placing a live order."""
    tradingsymbol = serializers.CharField()
    exchange = serializers.ChoiceField(
        choices=["NSE", "BSE", "NFO", "MCX"],
        default="NSE",
    )
    transaction_type = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    order_type = serializers.ChoiceField(
        choices=["MARKET", "LIMIT", "SL", "SL-M"],
        default="MARKET",
    )
    product = serializers.ChoiceField(
        choices=["MIS", "NRML", "CNC"],
        default="MIS",
    )
    price = serializers.FloatField(default=0)
    trigger_price = serializers.FloatField(default=0)
    tag = serializers.CharField(default="", allow_blank=True)
```

### .\backend\apps\zerodha\api\urls.py
```python
from django.urls import path

from .views import (
    ZerodhaConfigAPIView,
    ZerodhaFundsAPIView,
    ZerodhaHoldingsAPIView,
    ZerodhaLoginURLAPIView,
    ZerodhaLogoutAPIView,
    ZerodhaOrderCancelAPIView,
    ZerodhaOrderListAPIView,
    ZerodhaPositionsAPIView,
    ZerodhaProfileAPIView,
    ZerodhaStatusAPIView,
    ZerodhaTokenExchangeAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    path(
        "status/",
        ZerodhaStatusAPIView.as_view(),
        name="zerodha-status",
    ),
    path(
        "config/",
        ZerodhaConfigAPIView.as_view(),
        name="zerodha-config",
    ),
    path(
        "login-url/",
        ZerodhaLoginURLAPIView.as_view(),
        name="zerodha-login-url",
    ),
    path(
        "token/",
        ZerodhaTokenExchangeAPIView.as_view(),
        name="zerodha-token",
    ),
    path(
        "logout/",
        ZerodhaLogoutAPIView.as_view(),
        name="zerodha-logout",
    ),

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------
    path(
        "profile/",
        ZerodhaProfileAPIView.as_view(),
        name="zerodha-profile",
    ),
    path(
        "funds/",
        ZerodhaFundsAPIView.as_view(),
        name="zerodha-funds",
    ),

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    path(
        "orders/",
        ZerodhaOrderListAPIView.as_view(),
        name="zerodha-orders",
    ),
    path(
        "orders/<str:order_id>/cancel/",
        ZerodhaOrderCancelAPIView.as_view(),
        name="zerodha-order-cancel",
    ),

    # ------------------------------------------------------------------
    # Positions & Holdings
    # ------------------------------------------------------------------
    path(
        "positions/",
        ZerodhaPositionsAPIView.as_view(),
        name="zerodha-positions",
    ),
    path(
        "holdings/",
        ZerodhaHoldingsAPIView.as_view(),
        name="zerodha-holdings",
    ),
]
```

### .\backend\apps\zerodha\api\views.py
```python
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.auth_service import ZerodhaAuthService
from ..services.kite_service import KiteService
from .serializers import (
    OrderPlaceSerializer,
    TokenExchangeSerializer,
    ZerodhaConfigSerializer,
    ZerodhaConfigUpdateSerializer,
    ZerodhaSessionSerializer,
)

logger = logging.getLogger(__name__)


class ZerodhaStatusAPIView(APIView):
    """
    GET /api/zerodha/status/
    Return Zerodha connection status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            status = service.get_status()
            return ApiResponse.success(status)
        except Exception as e:
            logger.error(f"ZerodhaStatusAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch status.")


class ZerodhaConfigAPIView(APIView):
    """
    GET /api/zerodha/config/   — get config
    PUT /api/zerodha/config/   — save API key/secret
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            serializer = ZerodhaConfigSerializer(service.config)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"ZerodhaConfigAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch config.")

    def put(self, request):
        serializer = ZerodhaConfigUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            service = ZerodhaAuthService(request.user)
            config = service.save_config(serializer.validated_data)
            return ApiResponse.success(
                data=ZerodhaConfigSerializer(config).data,
                message="Zerodha config saved.",
            )
        except Exception as e:
            logger.error(f"ZerodhaConfigAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to save config.")


class ZerodhaLoginURLAPIView(APIView):
    """
    GET /api/zerodha/login-url/
    Get the Kite Connect login URL.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            url = service.get_login_url()
            return ApiResponse.success(
                data={"login_url": url},
                message="Visit this URL to login to Zerodha.",
            )
        except ValueError as e:
            return ApiResponse.error(message=str(e))
        except Exception as e:
            logger.error(f"ZerodhaLoginURLAPIView error: {e}")
            return ApiResponse.error(message="Failed to generate login URL.")


class ZerodhaTokenExchangeAPIView(APIView):
    """
    POST /api/zerodha/token/
    Exchange request token for access token.
    Called after Kite Connect login redirect.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TokenExchangeSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            service = ZerodhaAuthService(request.user)
            result = service.exchange_token(
                serializer.validated_data["request_token"]
            )
            return ApiResponse.success(
                data=result,
                message="Zerodha login successful.",
            )
        except Exception as e:
            logger.error(f"ZerodhaTokenExchangeAPIView error: {e}")
            return ApiResponse.error(
                message=f"Token exchange failed: {str(e)}"
            )


class ZerodhaLogoutAPIView(APIView):
    """
    POST /api/zerodha/logout/
    Logout from Zerodha and revoke access token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            service = ZerodhaAuthService(request.user)
            result = service.logout()
            return ApiResponse.success(message=result["message"])
        except Exception as e:
            logger.error(f"ZerodhaLogoutAPIView error: {e}")
            return ApiResponse.error(message="Logout failed.")


class ZerodhaProfileAPIView(APIView):
    """
    GET /api/zerodha/profile/
    Fetch Zerodha user profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            profile = service.get_profile()
            return ApiResponse.success(profile)
        except Exception as e:
            logger.error(f"ZerodhaProfileAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch profile.")


class ZerodhaFundsAPIView(APIView):
    """
    GET /api/zerodha/funds/
    Fetch available funds and margins.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            funds = service.get_funds()
            return ApiResponse.success(funds)
        except Exception as e:
            logger.error(f"ZerodhaFundsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch funds.")


class ZerodhaOrderListAPIView(APIView):
    """
    GET  /api/zerodha/orders/  — list today's orders
    POST /api/zerodha/orders/  — place a live order
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            orders = service.get_orders()
            return ApiResponse.success(orders)
        except Exception as e:
            logger.error(f"ZerodhaOrderListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch orders.")

    def post(self, request):
        serializer = OrderPlaceSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid order data.",
                errors=serializer.errors,
            )
        try:
            service = KiteService(request.user)
            result = service.place_order(serializer.validated_data)
            return ApiResponse.success(
                data=result,
                message="Order placed.",
            )
        except Exception as e:
            logger.error(f"ZerodhaOrderListAPIView POST error: {e}")
            return ApiResponse.error(message=f"Order failed: {str(e)}")


class ZerodhaOrderCancelAPIView(APIView):
    """
    POST /api/zerodha/orders/<order_id>/cancel/
    Cancel a live order.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id: str):
        try:
            service = KiteService(request.user)
            result = service.cancel_order(order_id)
            return ApiResponse.success(
                data=result,
                message="Order cancelled.",
            )
        except Exception as e:
            logger.error(f"ZerodhaOrderCancelAPIView error: {e}")
            return ApiResponse.error(message=f"Cancel failed: {str(e)}")


class ZerodhaPositionsAPIView(APIView):
    """
    GET /api/zerodha/positions/
    Fetch current live positions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            positions = service.get_positions()
            return ApiResponse.success(positions)
        except Exception as e:
            logger.error(f"ZerodhaPositionsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch positions.")


class ZerodhaHoldingsAPIView(APIView):
    """
    GET /api/zerodha/holdings/
    Fetch long-term holdings.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = KiteService(request.user)
            holdings = service.get_holdings()
            return ApiResponse.success(holdings)
        except Exception as e:
            logger.error(f"ZerodhaHoldingsAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch holdings.")
```

### .\backend\config\urls.py
```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger",),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/market/", include("apps.market_data.api.urls"),),
    path("api/strategies/", include("apps.strategies.api.urls")),
    path("api/ai/", include("apps.ai_engine.api.urls")),
    path("api/paper/", include("apps.paper_trading.api.urls")),
    path("api/journal/", include("apps.journal.api.urls")),
    path("api/backtest/", include("apps.backtesting.api.urls")),
    path("api/knowledge/", include("apps.knowledge.api.urls")),
    path("api/notifications/", include("apps.notifications.api.urls")),
    path("api/zerodha/", include("apps.zerodha.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### .\backend\shared\permissions.py
```python
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff


class IsSuperUser(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser
```

## 9. Base & Layout Templates (Frontend Foundation)

### BASE: .\backend\templates\base.html
```html
{% load static %}
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>
        {% block title %}
        Athena AI Trading Platform
        {% endblock %}
    </title>

    <!-- Bootstrap -->

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/css/bootstrap.min.css"
          rel="stylesheet">

    <!-- Bootstrap Icons -->

    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

    <!-- Google Font -->

    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet">

    <!-- Site CSS -->

    <link rel="stylesheet"
          href="{% static 'css/style.css' %}">

    {% block css %}
    {% endblock %}

</head>

<body>

    <div id="app">

        {% block content %}
        {% endblock %}

    </div>

    <!-- Bootstrap -->

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/js/bootstrap.bundle.min.js">
    </script>

    <!-- Axios -->

    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js">
    </script>

    <!-- Common JS -->

    <script src="{% static 'js/app.js' %}">
    </script>

    {% block javascript %}
    {% endblock %}

</body>

</html>
```

## 10. All HTML Templates (per app)

### .\frontend\index.html
```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Athena AI Trading Platform</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet" />
</head>
<body class="bg-dark-950 text-dark-100 antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

## 11. Custom CSS Files

### .\frontend\index.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
    * {
        box-sizing: border-box;
    }

    body {
        @apply bg-dark-950 text-dark-100 font-sans;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        @apply bg-dark-900;
    }

    ::-webkit-scrollbar-thumb {
        @apply bg-dark-600 rounded-full;
    }

        ::-webkit-scrollbar-thumb:hover {
            @apply bg-dark-500;
        }
}

@layer components {
    .card {
        @apply bg-dark-900 border border-dark-700 rounded-xl p-4;
    }

    .card-header {
        @apply flex items-center justify-between mb-4;
    }

    .card-title {
        @apply text-sm font-semibold text-dark-200 uppercase tracking-wider;
    }

    .btn {
        @apply inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-950 disabled:opacity-50 disabled:cursor-not-allowed;
    }

    .btn-primary {
        @apply btn bg-primary-600 hover:bg-primary-500 text-white focus:ring-primary-500;
    }

    .btn-secondary {
        @apply btn bg-dark-700 hover:bg-dark-600 text-dark-100 focus:ring-dark-500;
    }

    .btn-danger {
        @apply btn bg-red-600 hover:bg-red-500 text-white focus:ring-red-500;
    }

    .btn-success {
        @apply btn bg-green-600 hover:bg-green-500 text-white focus:ring-green-500;
    }

    .btn-ghost {
        @apply btn bg-transparent hover:bg-dark-800 text-dark-300 hover:text-dark-100;
    }

    .btn-sm {
        @apply px-3 py-1.5 text-xs;
    }

    .btn-lg {
        @apply px-6 py-3 text-base;
    }

    .input {
        @apply w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all;
    }

    .label {
        @apply block text-xs font-medium text-dark-400 mb-1.5;
    }

    .badge {
        @apply inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium;
    }

    .badge-green {
        @apply badge bg-green-900/50 text-green-400 border border-green-800;
    }

    .badge-red {
        @apply badge bg-red-900/50 text-red-400 border border-red-800;
    }

    .badge-yellow {
        @apply badge bg-yellow-900/50 text-yellow-400 border border-yellow-800;
    }

    .badge-blue {
        @apply badge bg-blue-900/50 text-blue-400 border border-blue-800;
    }

    .badge-gray {
        @apply badge bg-dark-800 text-dark-400 border border-dark-700;
    }

    .table-wrapper {
        @apply overflow-x-auto rounded-xl border border-dark-700;
    }

    .table {
        @apply w-full text-sm text-left;
    }

        .table thead {
            @apply bg-dark-800 text-dark-400 text-xs uppercase tracking-wider;
        }

            .table thead th {
                @apply px-4 py-3 font-medium;
            }

        .table tbody tr {
            @apply border-t border-dark-800 hover:bg-dark-800/50 transition-colors;
        }

        .table tbody td {
            @apply px-4 py-3 text-dark-200;
        }

    .positive {
        @apply text-green-400;
    }

    .negative {
        @apply text-red-400;
    }

    .neutral {
        @apply text-dark-400;
    }

    .page-title {
        @apply text-xl font-bold text-dark-50;
    }

    .page-subtitle {
        @apply text-sm text-dark-400 mt-1;
    }

    .section-title {
        @apply text-base font-semibold text-dark-100 mb-3;
    }

    .stat-value {
        @apply text-2xl font-bold text-dark-50;
    }

    .stat-label {
        @apply text-xs text-dark-500 mt-1;
    }

    .divider {
        @apply border-t border-dark-800 my-4;
    }
}

```

### .\frontend\src\index.css
```css

```

## 12. Custom JavaScript Files

### .\frontend\postcss.config.js
```javascript
export default {
    plugins: {
        tailwindcss: {},
        autoprefixer: {},
    },
};
```

### .\frontend\tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: "#eff6ff",
                    100: "#dbeafe",
                    200: "#bfdbfe",
                    300: "#93c5fd",
                    400: "#60a5fa",
                    500: "#3b82f6",
                    600: "#2563eb",
                    700: "#1d4ed8",
                    800: "#1e40af",
                    900: "#1e3a8a",
                },
                dark: {
                    50: "#f8fafc",
                    100: "#f1f5f9",
                    200: "#e2e8f0",
                    300: "#cbd5e1",
                    400: "#94a3b8",
                    500: "#64748b",
                    600: "#475569",
                    700: "#334155",
                    800: "#1e293b",
                    900: "#0f172a",
                    950: "#020617",
                },
                success: "#22c55e",
                danger: "#ef4444",
                warning: "#f59e0b",
                info: "#3b82f6",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
        },
    },
    plugins: [],
};
```

### .\frontend\vite.config.js
```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
            "/ws": {
                target: "ws://127.0.0.1:8000",
                ws: true,
            },
        },
    },
});
```

### .\frontend\src\api\analysis.js
```javascript
import api from "./axios";

export const analysisAPI = {
    analyze: (data) =>
        api.post("/ai/analyze/", data),

    getSessions: () =>
        api.get("/ai/sessions/"),

    getSession: (id) =>
        api.get(`/ai/sessions/${id}/`),

    getSignals: () =>
        api.get("/ai/signals/"),

    getTemplates: () =>
        api.get("/ai/templates/"),
};
```

### .\frontend\src\api\auth.js
```javascript
import api from "./axios";

export const authAPI = {
    login: (credentials) =>
        api.post("/accounts/login/", credentials),

    logout: (refresh) =>
        api.post("/accounts/logout/", { refresh }),

    profile: () =>
        api.get("/accounts/profile/"),

    refreshToken: (refresh) =>
        api.post("/accounts/token/refresh/", { refresh }),
};
```

### .\frontend\src\api\axios.js
```javascript
import axios from "axios";
import useAuthStore from "../store/authStore";

const api = axios.create({
    baseURL: "/api",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor — attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor — handle auth errors
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;

        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;

            try {
                const refreshToken = useAuthStore.getState().refreshToken;

                if (!refreshToken) {
                    useAuthStore.getState().logout();
                    window.location.href = "/login";
                    return Promise.reject(error);
                }

                const response = await axios.post("/api/accounts/token/refresh/", {
                    refresh: refreshToken,
                });

                const { access } = response.data;
                useAuthStore.getState().setAccessToken(access);
                original.headers.Authorization = `Bearer ${access}`;

                return api(original);
            } catch {
                useAuthStore.getState().logout();
                window.location.href = "/login";
                return Promise.reject(error);
            }
        }

        return Promise.reject(error);
    }
);

export default api;
```

### .\frontend\src\api\backtesting.js
```javascript
import api from "./axios";

export const backtestingAPI = {
    getRuns: (params) =>
        api.get("/backtest/runs/", { params }),

    createRun: (data) =>
        api.post("/backtest/runs/", data),

    getRun: (id) =>
        api.get(`/backtest/runs/${id}/`),

    getTrades: (id) =>
        api.get(`/backtest/runs/${id}/trades/`),
};
```

### .\frontend\src\api\journal.js
```javascript
import api from "./axios";

export const journalAPI = {
    getEntries: (params) =>
        api.get("/journal/entries/", { params }),

    createEntry: (data) =>
        api.post("/journal/entries/", data),

    getEntry: (id) =>
        api.get(`/journal/entries/${id}/`),

    updateEntry: (id, data) =>
        api.put(`/journal/entries/${id}/`, data),

    deleteEntry: (id) =>
        api.delete(`/journal/entries/${id}/`),

    getAIReview: (id) =>
        api.post(`/journal/entries/${id}/review/`),

    getTradeNotes: (id) =>
        api.get(`/journal/entries/${id}/notes/`),

    addTradeNote: (id, data) =>
        api.post(`/journal/entries/${id}/notes/`, data),

    getStats: () =>
        api.get("/journal/stats/"),

    getMistakes: () =>
        api.get("/journal/mistakes/"),

    getLessons: (params) =>
        api.get("/journal/lessons/", { params }),

    addLesson: (data) =>
        api.post("/journal/lessons/", data),

    reinforceLesson: (id) =>
        api.post(`/journal/lessons/${id}/reinforce/`),

    getRules: () =>
        api.get("/journal/rules/"),
};
```

### .\frontend\src\api\knowledge.js
```javascript
import api from "./axios";

export const knowledgeAPI = {
    search: (q) =>
        api.get("/knowledge/search/", { params: { q } }),

    getTags: () =>
        api.get("/knowledge/tags/"),

    getArticles: (params) =>
        api.get("/knowledge/articles/", { params }),

    createArticle: (data) =>
        api.post("/knowledge/articles/", data),

    getArticle: (slug) =>
        api.get(`/knowledge/articles/${slug}/`),

    updateArticle: (slug, data) =>
        api.put(`/knowledge/articles/${slug}/`, data),

    deleteArticle: (slug) =>
        api.delete(`/knowledge/articles/${slug}/`),

    summarizeArticle: (slug) =>
        api.post(`/knowledge/articles/${slug}/summarize/`),

    getBooks: () =>
        api.get("/knowledge/books/"),

    createBook: (data) =>
        api.post("/knowledge/books/", data),

    getRules: (params) =>
        api.get("/knowledge/rules/", { params }),

    createRule: (data) =>
        api.post("/knowledge/rules/", data),

    updateRule: (id, data) =>
        api.put(`/knowledge/rules/${id}/`, data),

    deleteRule: (id) =>
        api.delete(`/knowledge/rules/${id}/`),

    recordRuleBroken: (id) =>
        api.post(`/knowledge/rules/${id}/broken/`),

    getPrompts: (params) =>
        api.get("/knowledge/prompts/", { params }),

    createPrompt: (data) =>
        api.post("/knowledge/prompts/", data),

    usePrompt: (id) =>
        api.post(`/knowledge/prompts/${id}/use/`),
};
```

### .\frontend\src\api\market.js
```javascript
import api from "./axios";

export const marketAPI = {
    // Instruments
    getInstruments: (params) =>
        api.get("/market/instruments/", { params }),

    searchInstruments: (q) =>
        api.get("/market/instruments/search/", { params: { q } }),

    getInstrument: (symbol) =>
        api.get(`/market/instruments/${symbol}/`),

    // Indices
    getIndices: () =>
        api.get("/market/indices/"),

    // Quotes
    getQuotes: () =>
        api.get("/market/quotes/"),

    getQuote: (symbol) =>
        api.get(`/market/quotes/${symbol}/`),

    getBulkQuotes: (symbols) =>
        api.post("/market/quotes/bulk/", { symbols }),

    // Historical
    getHistorical: (symbol, params) =>
        api.get(`/market/historical/${symbol}/`, { params }),

    // Expiry
    getExpiry: (symbol) =>
        api.get(`/market/expiry/${symbol}/`),

    // Option Chain
    getOptionChain: (symbol) =>
        api.get(`/market/option-chain/${symbol}/`),

    // Session
    getSession: () =>
        api.get("/market/session/"),

    getEngineStatus: () =>
        api.get("/market/engine/status/"),

    // Indicators
    getIndicatorList: () =>
        api.get("/market/indicators/"),

    calculateIndicators: (data) =>
        api.post("/market/indicators/calculate/", data),
};
```

### .\frontend\src\api\notifications.js
```javascript
import api from "./axios";

export const notificationsAPI = {
    getNotifications: (params) =>
        api.get("/notifications/", { params }),

    markRead: (id) =>
        api.post(`/notifications/${id}/read/`),

    markAllRead: () =>
        api.post("/notifications/read-all/"),

    getPreferences: () =>
        api.get("/notifications/preferences/"),

    updatePreferences: (data) =>
        api.put("/notifications/preferences/", data),

    getAlerts: () =>
        api.get("/notifications/alerts/"),

    createAlert: (data) =>
        api.post("/notifications/alerts/", data),

    cancelAlert: (id) =>
        api.post(`/notifications/alerts/${id}/cancel/`),

    checkAlerts: () =>
        api.post("/notifications/alerts/check/"),
};
```

### .\frontend\src\api\paper.js
```javascript
import api from "./axios";

export const paperAPI = {
    getPortfolio: () =>
        api.get("/paper/portfolio/"),

    resetPortfolio: () =>
        api.post("/paper/portfolio/reset/"),

    getOrders: (params) =>
        api.get("/paper/orders/", { params }),

    placeOrder: (data) =>
        api.post("/paper/orders/", data),

    getTodayOrders: () =>
        api.get("/paper/orders/today/"),

    cancelOrder: (id) =>
        api.post(`/paper/orders/${id}/cancel/`),

    getPositions: () =>
        api.get("/paper/positions/"),

    getTrades: (params) =>
        api.get("/paper/trades/", { params }),

    getTodayTrades: () =>
        api.get("/paper/trades/today/"),
};
```

### .\frontend\src\api\strategies.js
```javascript
import api from "./axios";

export const strategiesAPI = {
    getStrategies: () =>
        api.get("/strategies/"),

    createStrategy: (data) =>
        api.post("/strategies/", data),

    getStrategy: (id) =>
        api.get(`/strategies/${id}/`),

    updateStrategy: (id, data) =>
        api.put(`/strategies/${id}/`, data),

    deleteStrategy: (id) =>
        api.delete(`/strategies/${id}/`),

    runStrategy: (data) =>
        api.post("/strategies/run/", data),

    runAll: (symbols) =>
        api.post("/strategies/run-all/", { symbols }),

    getSignals: (params) =>
        api.get("/strategies/signals/", { params }),

    getSignalsBySymbol: (symbol) =>
        api.get(`/strategies/signals/${symbol}/`),
};
```

### .\frontend\src\api\zerodha.js
```javascript
import api from "./axios";

export const zerodhaAPI = {
    getStatus: () =>
        api.get("/zerodha/status/"),

    getConfig: () =>
        api.get("/zerodha/config/"),

    saveConfig: (data) =>
        api.put("/zerodha/config/", data),

    getLoginUrl: () =>
        api.get("/zerodha/login-url/"),

    exchangeToken: (request_token) =>
        api.post("/zerodha/token/", { request_token }),

    logout: () =>
        api.post("/zerodha/logout/"),

    getProfile: () =>
        api.get("/zerodha/profile/"),

    getFunds: () =>
        api.get("/zerodha/funds/"),

    getOrders: () =>
        api.get("/zerodha/orders/"),

    placeOrder: (data) =>
        api.post("/zerodha/orders/", data),

    cancelOrder: (orderId) =>
        api.post(`/zerodha/orders/${orderId}/cancel/`),

    getPositions: () =>
        api.get("/zerodha/positions/"),

    getHoldings: () =>
        api.get("/zerodha/holdings/"),
};
```

### .\frontend\src\components\charts\index.js
```javascript

```

### .\frontend\src\components\common\index.js
```javascript
export { default as Button } from "./Button";
export { default as Card } from "./Card";
export { default as Badge } from "./Badge";
export { default as Modal } from "./Modal";
export { default as Table } from "./Table";
export { default as Spinner } from "./Spinner";
export { default as Alert } from "./Alert";
export { default as Input } from "./Input";
export { default as Select } from "./Select";
export { default as EmptyState } from "./EmptyState";
```

### .\frontend\src\components\layout\index.js
```javascript
export { default as Sidebar } from "./Sidebar";
export { default as Topbar } from "./Topbar";
export { default as PageWrapper } from "./PageWrapper";
export { default as AuthLayout } from "./AuthLayout";
```

### .\frontend\src\hooks\useAuth.js
```javascript
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../api/auth";
import useAuthStore from "../store/authStore";

export function useLogin() {
    const { login } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: (credentials) => authAPI.login(credentials),
        onSuccess: (response) => {
            login(response.data);
            navigate("/dashboard");
        },
    });
}

export function useLogout() {
    const { logout, refreshToken } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: () => authAPI.logout(refreshToken),
        onSettled: () => {
            logout();
            navigate("/login");
        },
    });
}
```

### .\frontend\src\hooks\useMarket.js
```javascript
import { useQuery } from "@tanstack/react-query";
import { marketAPI } from "../api/market";
import useMarketStore from "../store/marketStore";
import { useEffect } from "react";

export function useSession() {
    const { setSession } = useMarketStore();

    const query = useQuery({
        queryKey: ["session"],
        queryFn: () => marketAPI.getSession(),
        refetchInterval: 60000,
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (query.data) setSession(query.data);
    }, [query.data]);

    return query;
}

export function useQuotes() {
    return useQuery({
        queryKey: ["quotes"],
        queryFn: () => marketAPI.getQuotes(),
        refetchInterval: 5000,
        select: (res) => res.data.data,
    });
}

export function useQuote(symbol) {
    return useQuery({
        queryKey: ["quote", symbol],
        queryFn: () => marketAPI.getQuote(symbol),
        refetchInterval: 5000,
        select: (res) => res.data.data,
        enabled: !!symbol,
    });
}

export function useIndices() {
    return useQuery({
        queryKey: ["indices"],
        queryFn: () => marketAPI.getIndices(),
        refetchInterval: 10000,
        select: (res) => res.data.data,
    });
}

export function useHistorical(symbol, timeframe, limit = 100) {
    return useQuery({
        queryKey: ["historical", symbol, timeframe, limit],
        queryFn: () =>
            marketAPI.getHistorical(symbol, { timeframe, limit }),
        select: (res) => res.data.data,
        enabled: !!symbol && !!timeframe,
    });
}
```

### .\frontend\src\hooks\useNotifications.js
```javascript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationsAPI } from "../api/notifications";
import useNotificationStore from "../store/notificationStore";
import { useEffect } from "react";

export function useNotifications(params = {}) {
    const { setNotifications, setUnreadCount } = useNotificationStore();

    const query = useQuery({
        queryKey: ["notifications", params],
        queryFn: () => notificationsAPI.getNotifications(params),
        refetchInterval: 30000,
        select: (res) => res.data.data,
    });

    useEffect(() => {
        if (query.data) {
            setNotifications(query.data.notifications || []);
            setUnreadCount(query.data.unread_count || 0);
        }
    }, [query.data]);

    return query;
}

export function useMarkRead() {
    const queryClient = useQueryClient();
    const { markRead } = useNotificationStore();

    return useMutation({
        mutationFn: (id) => notificationsAPI.markRead(id),
        onSuccess: (_, id) => {
            markRead(id);
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });
}

export function useMarkAllRead() {
    const queryClient = useQueryClient();
    const { markAllRead } = useNotificationStore();

    return useMutation({
        mutationFn: () => notificationsAPI.markAllRead(),
        onSuccess: () => {
            markAllRead();
            queryClient.invalidateQueries({ queryKey: ["notifications"] });
        },
    });
}
```

### .\frontend\src\hooks\useWebSocket.js
```javascript
import { useEffect, useRef, useCallback } from "react";
import useAuthStore from "../store/authStore";
import useMarketStore from "../store/marketStore";

export function useMarketWebSocket(symbol = null) {
    const ws = useRef(null);
    const { accessToken } = useAuthStore();
    const { setQuote, setSession } = useMarketStore();

    const connect = useCallback(() => {
        const url = symbol
            ? `ws://127.0.0.1:8000/ws/market/quotes/${symbol}/`
            : `ws://127.0.0.1:8000/ws/market/quotes/`;

        ws.current = new WebSocket(url);

        ws.current.onopen = () => {
            console.log("WebSocket connected");
        };

        ws.current.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                if (message.type === "tick") {
                    const tick = message.data;
                    setQuote(tick.symbol, tick);
                }

                if (message.type === "session") {
                    setSession(message.data);
                }
            } catch (e) {
                console.error("WebSocket parse error:", e);
            }
        };

        ws.current.onclose = () => {
            console.log("WebSocket closed — reconnecting in 5s");
            setTimeout(connect, 5000);
        };

        ws.current.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }, [symbol, setQuote, setSession]);

    useEffect(() => {
        if (accessToken) {
            connect();
        }

        return () => {
            if (ws.current) {
                ws.current.onclose = null;
                ws.current.close();
            }
        };
    }, [connect, accessToken]);

    const sendMessage = useCallback((message) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
        }
    }, []);

    return { sendMessage };
}
```

### .\frontend\src\store\authStore.js
```javascript
import { create } from "zustand";
import { persist } from "zustand/middleware";

const useAuthStore = create(
    persist(
        (set, get) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            login: (data) =>
                set({
                    user: data.user,
                    accessToken: data.access,
                    refreshToken: data.refresh,
                    isAuthenticated: true,
                }),

            logout: () =>
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                }),

            setAccessToken: (token) =>
                set({ accessToken: token }),

            setUser: (user) =>
                set({ user }),
        }),
        {
            name: "athena-auth",
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
);

export default useAuthStore;
```

### .\frontend\src\store\marketStore.js
```javascript
import { create } from "zustand";

const useMarketStore = create((set, get) => ({
    quotes: {},
    session: null,
    isLive: false,
    selectedSymbol: "NIFTY",
    selectedTimeframe: "15m",

    setQuote: (symbol, quote) =>
        set((state) => ({
            quotes: { ...state.quotes, [symbol]: quote },
        })),

    setQuotes: (quotes) =>
        set({ quotes }),

    setSession: (session) =>
        set({
            session,
            isLive: session?.is_live || false,
        }),

    setSelectedSymbol: (symbol) =>
        set({ selectedSymbol: symbol }),

    setSelectedTimeframe: (timeframe) =>
        set({ selectedTimeframe: timeframe }),

    getQuote: (symbol) =>
        get().quotes[symbol] || null,
}));

export default useMarketStore;
```

### .\frontend\src\store\notificationStore.js
```javascript
import { create } from "zustand";

const useNotificationStore = create((set, get) => ({
    notifications: [],
    unreadCount: 0,

    setNotifications: (notifications) =>
        set({ notifications }),

    setUnreadCount: (count) =>
        set({ unreadCount: count }),

    addNotification: (notification) =>
        set((state) => ({
            notifications: [notification, ...state.notifications],
            unreadCount: state.unreadCount + 1,
        })),

    markRead: (id) =>
        set((state) => ({
            notifications: state.notifications.map((n) =>
                n.id === id ? { ...n, status: "READ" } : n
            ),
            unreadCount: Math.max(0, state.unreadCount - 1),
        })),

    markAllRead: () =>
        set((state) => ({
            notifications: state.notifications.map((n) => ({
                ...n,
                status: "READ",
            })),
            unreadCount: 0,
        })),
}));

export default useNotificationStore;
```

### .\frontend\src\store\uiStore.js
```javascript
import { create } from "zustand";

const useUIStore = create((set) => ({
    sidebarOpen: true,
    theme: "dark",
    loading: false,

    toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    setSidebarOpen: (open) =>
        set({ sidebarOpen: open }),

    setLoading: (loading) =>
        set({ loading }),
}));

export default useUIStore;
```

### .\frontend\src\utils\constants.js
```javascript
export const APP_NAME = "Athena AI";
export const APP_VERSION = "1.0.0";

export const TIMEFRAMES = [
    { value: "1m", label: "1 Min" },
    { value: "3m", label: "3 Min" },
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
    { value: "1h", label: "1 Hour" },
    { value: "1d", label: "1 Day" },
];

export const INDICES = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
];

export const EXCHANGES = [
    { value: "NSE", label: "NSE" },
    { value: "BSE", label: "BSE" },
    { value: "NFO", label: "NFO" },
    { value: "MCX", label: "MCX" },
];

export const SIGNAL_COLORS = {
    BUY: "text-green-400",
    SELL: "text-red-400",
    NEUTRAL: "text-dark-400",
    NO_SETUP: "text-dark-400",
    WATCH: "text-yellow-400",
};

export const SIGNAL_BADGES = {
    BUY: "badge-green",
    SELL: "badge-red",
    NEUTRAL: "badge-gray",
    NO_SETUP: "badge-gray",
    WATCH: "badge-yellow",
};

export const CONFIDENCE_COLORS = {
    HIGH: "text-green-400",
    MEDIUM: "text-yellow-400",
    LOW: "text-red-400",
};

export const SESSION_COLORS = {
    LIVE: "text-green-400",
    PRE_OPEN: "text-yellow-400",
    CLOSED: "text-dark-400",
};

export const INDICATORS = [
    "EMA_9",
    "EMA_21",
    "EMA_50",
    "RSI_14",
    "MACD",
    "BB_20",
    "VWAP",
    "ATR_14",
    "CPR",
];
```

### .\frontend\src\utils\formatters.js
```javascript
// Currency formatter (INR)
export const formatCurrency = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";

    const abs = Math.abs(num);
    let formatted;

    if (abs >= 10000000) {
        formatted = (num / 10000000).toFixed(2) + " Cr";
    } else if (abs >= 100000) {
        formatted = (num / 100000).toFixed(2) + " L";
    } else if (abs >= 1000) {
        formatted = (num / 1000).toFixed(2) + " K";
    } else {
        formatted = num.toFixed(decimals);
    }

    return `₹${formatted}`;
};

// Raw number formatter
export const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";
    return num.toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
};

// Percentage formatter
export const formatPercent = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";
    const sign = num > 0 ? "+" : "";
    return `${sign}${num.toFixed(decimals)}%`;
};

// PnL formatter — returns value + color class
export const formatPnL = (value) => {
    if (value === null || value === undefined) return { text: "—", color: "neutral" };
    const num = parseFloat(value);
    if (isNaN(num)) return { text: "—", color: "neutral" };

    return {
        text: formatCurrency(Math.abs(num)),
        color: num > 0 ? "positive" : num < 0 ? "negative" : "neutral",
        sign: num > 0 ? "+" : num < 0 ? "-" : "",
    };
};

// Date formatter
export const formatDate = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
};

// Time formatter
export const formatTime = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
    });
};

// DateTime formatter
export const formatDateTime = (date) => {
    if (!date) return "—";
    return `${formatDate(date)} ${formatTime(date)}`;
};

// Relative time
export const formatRelativeTime = (date) => {
    if (!date) return "—";
    const now = new Date();
    const d = new Date(date);
    const diff = Math.floor((now - d) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return formatDate(date);
};

// Large number abbreviation
export const abbreviateNumber = (value) => {
    if (!value) return "0";
    const num = parseFloat(value);
    if (num >= 10000000) return (num / 10000000).toFixed(1) + "Cr";
    if (num >= 100000) return (num / 100000).toFixed(1) + "L";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
};
```

### .\frontend\src\utils\helpers.js
```javascript
// Get signal color class
export const getSignalColor = (signal) => {
    const colors = {
        BUY: "text-green-400",
        SELL: "text-red-400",
        NEUTRAL: "text-dark-400",
        NO_SETUP: "text-dark-400",
        WATCH: "text-yellow-400",
    };
    return colors[signal] || "text-dark-400";
};

// Get signal badge class
export const getSignalBadge = (signal) => {
    const badges = {
        BUY: "badge-green",
        SELL: "badge-red",
        NEUTRAL: "badge-gray",
        NO_SETUP: "badge-gray",
        WATCH: "badge-yellow",
    };
    return badges[signal] || "badge-gray";
};

// Get confidence color
export const getConfidenceColor = (confidence) => {
    const colors = {
        HIGH: "text-green-400",
        MEDIUM: "text-yellow-400",
        LOW: "text-red-400",
    };
    return colors[confidence] || "text-dark-400";
};

// Get session color
export const getSessionColor = (session) => {
    const colors = {
        LIVE: "text-green-400",
        PRE_OPEN: "text-yellow-400",
        CLOSED: "text-dark-400",
        HOLIDAY: "text-dark-500",
    };
    return colors[session] || "text-dark-400";
};

// Clamp value
export const clamp = (value, min, max) =>
    Math.min(Math.max(value, min), max);

// Truncate text
export const truncate = (text, maxLength = 100) => {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
};

// Debounce
export const debounce = (fn, delay) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
};

// Group array by key
export const groupBy = (array, key) =>
    array.reduce((result, item) => {
        const group = item[key];
        if (!result[group]) result[group] = [];
        result[group].push(item);
        return result;
    }, {});

// Sort array by key
export const sortBy = (array, key, direction = "asc") =>
    [...array].sort((a, b) => {
        if (direction === "asc") return a[key] > b[key] ? 1 : -1;
        return a[key] < b[key] ? 1 : -1;
    });

// Check if market is open (IST)
export const isMarketOpen = () => {
    const now = new Date();
    const ist = new Date(
        now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
    );
    const day = ist.getDay();
    const hours = ist.getHours();
    const minutes = ist.getMinutes();
    const time = hours * 60 + minutes;

    if (day === 0 || day === 6) return false;
    return time >= 555 && time <= 930; // 9:15 to 15:30
};
```

## 13. Frontend Component Inventory
```
Total templates     : 2
Extend base.html    : 0
Use DataTables      : 0
Use Charts          : 0
Use Modals          : 0
Have Forms          : 0

Per-template breakdown:
  .\backend\templates\base.html: [standalone]
  .\frontend\index.html: [standalone]
```
