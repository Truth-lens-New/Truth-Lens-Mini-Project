import 'storage_category.dart';

/// Represents a single file item returned from a scan.
class FileItem {
  final String path;
  final String name;
  final int sizeBytes;
  final DateTime modifiedAt;
  final StorageCategoryType category;
  /// Hex MD5/SHA-1 hash — populated only on deep scan pass, null otherwise.
  final String? contentHash;

  const FileItem({
    required this.path,
    required this.name,
    required this.sizeBytes,
    required this.modifiedAt,
    required this.category,
    this.contentHash,
  });

  factory FileItem.fromMap(Map<dynamic, dynamic> map) {
    final typeStr = map['category'] as String? ?? 'other';
    return FileItem(
      path: map['path'] as String? ?? '',
      name: map['name'] as String? ?? '',
      sizeBytes: (map['sizeBytes'] as num?)?.toInt() ?? 0,
      modifiedAt: DateTime.fromMillisecondsSinceEpoch(
        (map['modifiedAt'] as num?)?.toInt() ?? 0,
      ),
      category: StorageCategory.parseType(typeStr),
      contentHash: map['contentHash'] as String?,
    );
  }

  @override
  String toString() => 'FileItem(name: $name, size: $sizeBytes, path: $path)';
}
