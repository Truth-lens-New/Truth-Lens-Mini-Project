# Storage Analyzer — Flutter Android App

A Flutter-based Android storage analysis app that provides accurate, transparent, and privacy-first storage insights.

---

## Features (V1 Scaffold)

| Feature | Status |
|---------|--------|
| Overall storage stats (used / free / total) | ✅ |
| Category breakdown (images, videos, audio, docs, apps, cache, other) | ✅ |
| Large files listing | ✅ |
| Duplicate finder — size-based pass | ✅ |
| Duplicate finder — hash-confirmed deep pass | ✅ (toggle in UI) |
| Per-app storage breakdown | ✅ (accurate with permission; estimated fallback) |
| Permanent delete flow with confirmation | ✅ |
| 100% offline — no network / analytics | ✅ |

---

## Requirements

- **Flutter** ≥ 3.10.0
- **Dart** ≥ 3.0.0
- **Android** minSdk **28** (Android 9 Pie)
- **Target SDK** 34 (Android 14)

---

## Running the App

```bash
cd mobile
flutter pub get
flutter run
```

> Make sure an Android device or emulator is connected and `adb devices` shows it.

---

## Permissions

| Permission | Purpose | Required |
|-----------|---------|---------|
| `READ_EXTERNAL_STORAGE` (API ≤ 32) | Read media files on Android 9–12 | Yes (for full scan) |
| `READ_MEDIA_IMAGES` | Read images on Android 13+ | Yes |
| `READ_MEDIA_VIDEO` | Read videos on Android 13+ | Yes |
| `READ_MEDIA_AUDIO` | Read audio on Android 13+ | Yes |
| `MANAGE_EXTERNAL_STORAGE` | Full file-system access on Android 11+ | Optional (needed for non-media files) |
| `WRITE_EXTERNAL_STORAGE` (API ≤ 29) | Delete files on Android 9–10 | Needed for deletion |
| `PACKAGE_USAGE_STATS` | Per-app storage via `StorageStatsManager` | Optional (enable in Settings) |

> **Note:** `MANAGE_EXTERNAL_STORAGE` requires the user to grant access via **Settings → Apps → Special app access → All files access**. In a production Play Store app this requires a policy justification.

---

## Android Version Compatibility

| Android Version | API | Behavior |
|----------------|-----|---------|
| Android 9 (Pie) | 28 | Full file access; broad `READ_EXTERNAL_STORAGE` works |
| Android 10 (Q) | 29 | Scoped storage introduced (opt-out possible via `requestLegacyExternalStorage`); delete via MediaStore for own files |
| Android 11 (R) | 30 | Scoped storage enforced; `MANAGE_EXTERNAL_STORAGE` required for `/sdcard` traversal; MediaStore covers most media |
| Android 12/12L | 31–32 | Same as 11; `READ_EXTERNAL_STORAGE` still accepted |
| Android 13+ (Tiramisu+) | 33+ | Granular `READ_MEDIA_*` permissions replace broad storage; `MediaStore.Files` still accessible |

---

## How Accuracy Is Achieved

### Two-Pass Scanning

1. **Fast metadata pass (default):** Queries Android's `MediaStore` content provider for sizes and metadata. O(1) per query — near-instant.
2. **Deep hash pass (opt-in):** For duplicate candidates, computes SHA-256 of each file's bytes. Confirms true duplicates vs. coincidentally same-sized files. Files > 512 MB are skipped to keep it responsive.

### Storage Statistics

- `StatFs` on the internal storage path provides **total** and **available** bytes matching what Android Settings reports.
- MediaStore aggregates may differ slightly from Settings totals because:
  - MediaStore doesn't index files in private app directories.
  - System partitions and reserved storage are excluded from `StatFs` available space.

### Per-App Breakdown

- When `PACKAGE_USAGE_STATS` is granted: uses `StorageStatsManager` (API 26+) for **exact** app/data/cache sizes — the same source Android Settings uses.
- Otherwise: shows APK size from `ApplicationInfo.sourceDir` as **estimated**, with a UI indicator.

### Category Classification

| Category | Source |
|---------|--------|
| Images | `MediaStore.Images` |
| Videos | `MediaStore.Video` |
| Audio | `MediaStore.Audio` |
| Documents | `MediaStore.Files` filtered by MIME type |
| Apps | `PackageManager.getInstalledApplications` APK sizes |
| Cache | App-own cache dirs (`Context.cacheDir`) |
| Other | Not yet covered by above |

---

## Architecture

```
mobile/
├── lib/
│   ├── main.dart                          # App entry point + navigation
│   ├── models/                            # Pure Dart data models
│   │   ├── storage_stats.dart
│   │   ├── storage_category.dart
│   │   ├── file_item.dart
│   │   ├── app_storage_info.dart
│   │   └── duplicate_group.dart
│   ├── services/
│   │   ├── storage_scan_service.dart      # Abstract interface
│   │   └── method_channel_storage_service.dart  # MethodChannel impl
│   ├── screens/
│   │   ├── home_screen.dart               # Dashboard
│   │   ├── categories_screen.dart
│   │   ├── large_files_screen.dart
│   │   ├── duplicates_screen.dart
│   │   └── apps_screen.dart
│   ├── widgets/
│   │   ├── category_card.dart
│   │   ├── file_list_item.dart
│   │   └── storage_bar.dart
│   └── utils/
│       └── format_bytes.dart
│
└── android/
    └── app/src/main/kotlin/com/example/storage_analyzer/
        ├── MainActivity.kt
        └── StorageScanPlugin.kt           # MethodChannel handler
```

### Platform Channel

- **Channel name:** `com.example.storage_analyzer/scan`
- **Methods:** `getStorageStats`, `getCategoryBreakdown`, `getLargeFiles`, `getDuplicates`, `getAppStorageInfo`, `deleteFile`

---

## Limitations

- **Private app data** (`/data/data/<pkg>/`) is inaccessible to other apps without root — not reported.
- **System storage** (OS, firmware) is not broken down individually.
- **iOS:** Not yet implemented. This scaffold is Android-only.
- **Delete on Android 10+:** Only MediaStore-indexed files or app-owned files can be deleted without a full SAF intent flow. Protected files return `success: false` with an explanation.
- **Cache stats** only show this app's own cache size without `PACKAGE_USAGE_STATS`. System-wide cache requires the usage stats permission.

---

## Running Tests

```bash
cd mobile
flutter test
```

---

## License

Part of the TruthLens mini-project repository — developed for personal/academic use.
