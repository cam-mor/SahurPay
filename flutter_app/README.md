# SahurPay Flutter app

This is the cross-platform Flutter interface for SahurPay.

The first slice provides typed session models, Python JSON migration parsing,
the payment-history screen, and a responsive session detail screen. It uses
sample sessions until SQLite and the Python JSON file migration workflow are
connected.

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
