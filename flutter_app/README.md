# SahurPay Flutter app

This is the cross-platform Flutter interface for SahurPay.

The first slice provides typed session models, Python JSON migration parsing,
the payment-history screen, and a responsive session detail screen. It uses
sample sessions until SQLite and the Python JSON file migration workflow are
connected.

The basic interactive slice now also includes:

- Configurable people names
- Today's-date default with an editable date picker
- Session category and note fields
- Multiple store receipts in one session
- Store payer, category, and note fields
- Product name, quantity, unit price, category, and note fields
- Responsible-person selection
- Repeated product and store entry
- Exact per-person allocations and cent remainders
- Saving sessions to the local application document directory

The app migrates `../../data/sessions.json` or `../data/sessions.json` once
when it is run from the repository layout, and falls back to an empty history
otherwise.

## Run

```bash
flutter pub get
flutter run
```

## Verify

```bash
flutter analyze
flutter test
```

## Platform folders

- `android/` - Android app
- `ios/` - iPhone and iPad app
- `linux/` - Linux desktop app
- `macos/` - macOS desktop app
- `windows/` - Windows desktop app
