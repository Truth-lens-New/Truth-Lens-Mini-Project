import '../models/storage_stats.dart';
import '../models/storage_category.dart';
import '../models/file_item.dart';
import '../models/duplicate_group.dart';
import '../models/app_storage_info.dart';

/// Abstract interface for storage scanning operations.
///
/// Implementations communicate with native platform code via MethodChannel.
/// All methods are async and may throw [StorageScanException] on failure.
abstract class StorageScanService {
  /// Returns overall device storage statistics (total / available / used).
  Future<StorageStats> getStorageStats();

  /// Returns per-category aggregates for all media categories.
  Future<List<StorageCategory>> getCategoryBreakdown();

  /// Returns the [limit] largest files across all scanned locations.
  Future<List<FileItem>> getLargeFiles({int limit = 50});

  /// Returns duplicate candidate groups.
  ///
  /// [deepScan] — when true, the native side computes content hashes to
  /// confirm duplicates; when false only size-based grouping is returned.
  Future<List<DuplicateGroup>> getDuplicates({bool deepScan = false});

  /// Returns per-app storage breakdown.
  ///
  /// Where Android's [StorageStatsManager] is unavailable or permission is
  /// not granted, the returned [AppStorageInfo.isAccurate] will be false.
  Future<List<AppStorageInfo>> getAppStorageInfo();

  /// Requests deletion of the file at [path].
  ///
  /// Returns true on success. Callers should only invoke this after explicit
  /// user confirmation. The native side only deletes files accessible via
  /// MediaStore or SAF; protected paths return false with a reason message.
  Future<DeleteResult> deleteFile(String path);
}

/// Result of a delete operation.
class DeleteResult {
  final bool success;
  final String? message;

  const DeleteResult({required this.success, this.message});

  factory DeleteResult.fromMap(Map<dynamic, dynamic> map) {
    return DeleteResult(
      success: map['success'] as bool? ?? false,
      message: map['message'] as String?,
    );
  }
}

/// Thrown when a native scan operation fails.
class StorageScanException implements Exception {
  final String message;
  final String? code;

  const StorageScanException(this.message, {this.code});

  @override
  String toString() => 'StorageScanException[$code]: $message';
}
