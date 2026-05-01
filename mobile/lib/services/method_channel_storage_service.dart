import 'package:flutter/services.dart';

import '../models/storage_stats.dart';
import '../models/storage_category.dart';
import '../models/file_item.dart';
import '../models/duplicate_group.dart';
import '../models/app_storage_info.dart';
import 'storage_scan_service.dart';

/// Flutter-side implementation that delegates all heavy work to Kotlin via
/// [MethodChannel].
///
/// Channel name: `com.example.storage_analyzer/scan`
class MethodChannelStorageService implements StorageScanService {
  static const _channel =
      MethodChannel('com.example.storage_analyzer/scan');

  @override
  Future<StorageStats> getStorageStats() async {
    try {
      final result = await _channel.invokeMethod<Map>('getStorageStats');
      if (result == null) {
        throw const StorageScanException('getStorageStats returned null');
      }
      return StorageStats.fromMap(result);
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }

  @override
  Future<List<StorageCategory>> getCategoryBreakdown() async {
    try {
      final result =
          await _channel.invokeMethod<List>('getCategoryBreakdown');
      if (result == null) return [];
      return result
          .map((e) => StorageCategory.fromMap(e as Map<dynamic, dynamic>))
          .toList();
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }

  @override
  Future<List<FileItem>> getLargeFiles({int limit = 50}) async {
    try {
      final result = await _channel.invokeMethod<List>(
        'getLargeFiles',
        {'limit': limit},
      );
      if (result == null) return [];
      return result
          .map((e) => FileItem.fromMap(e as Map<dynamic, dynamic>))
          .toList();
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }

  @override
  Future<List<DuplicateGroup>> getDuplicates({bool deepScan = false}) async {
    try {
      final result = await _channel.invokeMethod<List>(
        'getDuplicates',
        {'deepScan': deepScan},
      );
      if (result == null) return [];
      return result
          .map((e) => DuplicateGroup.fromMap(e as Map<dynamic, dynamic>))
          .toList();
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }

  @override
  Future<List<AppStorageInfo>> getAppStorageInfo() async {
    try {
      final result =
          await _channel.invokeMethod<List>('getAppStorageInfo');
      if (result == null) return [];
      return result
          .map((e) => AppStorageInfo.fromMap(e as Map<dynamic, dynamic>))
          .toList();
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }

  @override
  Future<DeleteResult> deleteFile(String path) async {
    try {
      final result = await _channel.invokeMethod<Map>(
        'deleteFile',
        {'path': path},
      );
      if (result == null) {
        return const DeleteResult(success: false, message: 'No result');
      }
      return DeleteResult.fromMap(result);
    } on PlatformException catch (e) {
      throw StorageScanException(e.message ?? 'Unknown error',
          code: e.code);
    }
  }
}
