/// Media/file categories used throughout the app.
enum StorageCategoryType {
  images,
  videos,
  audio,
  documents,
  apps,
  cache,
  other,
}

extension StorageCategoryTypeX on StorageCategoryType {
  String get label {
    switch (this) {
      case StorageCategoryType.images:
        return 'Images';
      case StorageCategoryType.videos:
        return 'Videos';
      case StorageCategoryType.audio:
        return 'Audio';
      case StorageCategoryType.documents:
        return 'Documents';
      case StorageCategoryType.apps:
        return 'Apps';
      case StorageCategoryType.cache:
        return 'Cache';
      case StorageCategoryType.other:
        return 'Other';
    }
  }

  String get iconAsset {
    switch (this) {
      case StorageCategoryType.images:
        return 'assets/icons/images.png';
      case StorageCategoryType.videos:
        return 'assets/icons/videos.png';
      case StorageCategoryType.audio:
        return 'assets/icons/audio.png';
      case StorageCategoryType.documents:
        return 'assets/icons/documents.png';
      case StorageCategoryType.apps:
        return 'assets/icons/apps.png';
      case StorageCategoryType.cache:
        return 'assets/icons/cache.png';
      case StorageCategoryType.other:
        return 'assets/icons/other.png';
    }
  }
}

/// Aggregated size data for one storage category.
class StorageCategory {
  final StorageCategoryType type;
  final int totalBytes;
  final int fileCount;

  const StorageCategory({
    required this.type,
    required this.totalBytes,
    required this.fileCount,
  });

  factory StorageCategory.fromMap(Map<dynamic, dynamic> map) {
    final typeStr = map['type'] as String? ?? 'other';
    return StorageCategory(
      type: parseType(typeStr),
      totalBytes: (map['totalBytes'] as num?)?.toInt() ?? 0,
      fileCount: (map['fileCount'] as num?)?.toInt() ?? 0,
    );
  }

  static StorageCategoryType parseType(String raw) {
    switch (raw.toLowerCase()) {
      case 'images':
        return StorageCategoryType.images;
      case 'videos':
        return StorageCategoryType.videos;
      case 'audio':
        return StorageCategoryType.audio;
      case 'documents':
        return StorageCategoryType.documents;
      case 'apps':
        return StorageCategoryType.apps;
      case 'cache':
        return StorageCategoryType.cache;
      default:
        return StorageCategoryType.other;
    }
  }

  @override
  String toString() =>
      'StorageCategory(type: ${type.label}, bytes: $totalBytes, count: $fileCount)';
}
