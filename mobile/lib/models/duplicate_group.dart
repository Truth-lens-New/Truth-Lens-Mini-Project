import 'file_item.dart';

/// A group of files considered potential duplicates.
///
/// Phase 1: grouped by identical size.
/// Phase 2 (deep scan): grouped by identical content hash.
class DuplicateGroup {
  final int sizeBytes;
  final List<FileItem> files;
  /// Populated after deep (hash) scan; null means hash pass not yet run.
  final String? contentHash;

  const DuplicateGroup({
    required this.sizeBytes,
    required this.files,
    this.contentHash,
  });

  /// Wasted space = (n-1) * sizeBytes (keep one copy).
  int get wastedBytes => files.length > 1 ? (files.length - 1) * sizeBytes : 0;

  bool get isHashConfirmed => contentHash != null;

  factory DuplicateGroup.fromMap(Map<dynamic, dynamic> map) {
    final rawFiles = map['files'] as List<dynamic>? ?? [];
    return DuplicateGroup(
      sizeBytes: (map['sizeBytes'] as num?)?.toInt() ?? 0,
      files: rawFiles
          .map((f) => FileItem.fromMap(f as Map<dynamic, dynamic>))
          .toList(),
      contentHash: map['contentHash'] as String?,
    );
  }

  @override
  String toString() =>
      'DuplicateGroup(size: $sizeBytes, count: ${files.length}, hashConfirmed: $isHashConfirmed)';
}
