import 'package:flutter_test/flutter_test.dart';
import 'package:storage_analyzer/models/storage_stats.dart';
import 'package:storage_analyzer/models/storage_category.dart';
import 'package:storage_analyzer/models/file_item.dart';
import 'package:storage_analyzer/models/app_storage_info.dart';
import 'package:storage_analyzer/models/duplicate_group.dart';
import 'package:storage_analyzer/utils/format_bytes.dart';

void main() {
  group('StorageStats', () {
    test('fromMap computes usedBytes correctly', () {
      final stats = StorageStats.fromMap({
        'totalBytes': 128 * 1024 * 1024 * 1024,   // 128 GB
        'availableBytes': 32 * 1024 * 1024 * 1024, // 32 GB
      });
      expect(stats.totalBytes, equals(128 * 1024 * 1024 * 1024));
      expect(stats.availableBytes, equals(32 * 1024 * 1024 * 1024));
      expect(stats.usedBytes, equals(96 * 1024 * 1024 * 1024));
    });

    test('usedFraction is correct', () {
      final stats = StorageStats.fromMap({
        'totalBytes': 100,
        'availableBytes': 25,
      });
      expect(stats.usedFraction, closeTo(0.75, 0.001));
    });

    test('usedFraction is 0 when totalBytes is 0', () {
      final stats = StorageStats.fromMap({'totalBytes': 0, 'availableBytes': 0});
      expect(stats.usedFraction, equals(0.0));
    });

    test('handles missing fields gracefully', () {
      final stats = StorageStats.fromMap({});
      expect(stats.totalBytes, equals(0));
      expect(stats.availableBytes, equals(0));
      expect(stats.usedBytes, equals(0));
    });
  });

  group('StorageCategory', () {
    test('fromMap parses all known types', () {
      for (final entry in {
        'images': StorageCategoryType.images,
        'videos': StorageCategoryType.videos,
        'audio': StorageCategoryType.audio,
        'documents': StorageCategoryType.documents,
        'apps': StorageCategoryType.apps,
        'cache': StorageCategoryType.cache,
        'other': StorageCategoryType.other,
        'unknown_xyz': StorageCategoryType.other,
      }.entries) {
        final cat = StorageCategory.fromMap({
          'type': entry.key,
          'totalBytes': 1000,
          'fileCount': 5,
        });
        expect(cat.type, equals(entry.value),
            reason: 'type key: ${entry.key}');
      }
    });

    test('fromMap handles missing fields gracefully', () {
      final cat = StorageCategory.fromMap({});
      expect(cat.totalBytes, equals(0));
      expect(cat.fileCount, equals(0));
      expect(cat.type, equals(StorageCategoryType.other));
    });

    test('labels are non-empty', () {
      for (final type in StorageCategoryType.values) {
        expect(type.label, isNotEmpty);
      }
    });
  });

  group('FileItem', () {
    test('fromMap parses all fields correctly', () {
      final now = DateTime.now().millisecondsSinceEpoch;
      final item = FileItem.fromMap({
        'path': '/sdcard/DCIM/photo.jpg',
        'name': 'photo.jpg',
        'sizeBytes': 2 * 1024 * 1024,
        'modifiedAt': now,
        'category': 'images',
      });
      expect(item.path, equals('/sdcard/DCIM/photo.jpg'));
      expect(item.name, equals('photo.jpg'));
      expect(item.sizeBytes, equals(2 * 1024 * 1024));
      expect(item.category, equals(StorageCategoryType.images));
      expect(item.contentHash, isNull);
    });

    test('fromMap handles missing fields gracefully', () {
      final item = FileItem.fromMap({});
      expect(item.path, equals(''));
      expect(item.name, equals(''));
      expect(item.sizeBytes, equals(0));
    });
  });

  group('AppStorageInfo', () {
    test('totalBytes sums all fields', () {
      final app = AppStorageInfo.fromMap({
        'packageName': 'com.example.test',
        'appName': 'Test App',
        'appBytes': 50000000,
        'dataBytes': 10000000,
        'cacheBytes': 5000000,
        'isAccurate': true,
      });
      expect(app.totalBytes, equals(65000000));
      expect(app.isAccurate, isTrue);
    });

    test('isAccurate defaults to false when missing', () {
      final app = AppStorageInfo.fromMap({'packageName': 'com.test'});
      expect(app.isAccurate, isFalse);
    });
  });

  group('DuplicateGroup', () {
    test('wastedBytes is (n-1) * sizeBytes', () {
      final now = DateTime.now().millisecondsSinceEpoch;
      final group = DuplicateGroup.fromMap({
        'sizeBytes': 1024 * 1024,
        'contentHash': null,
        'files': [
          {'path': '/a', 'name': 'a', 'sizeBytes': 1024 * 1024,
           'modifiedAt': now, 'category': 'images'},
          {'path': '/b', 'name': 'b', 'sizeBytes': 1024 * 1024,
           'modifiedAt': now, 'category': 'images'},
          {'path': '/c', 'name': 'c', 'sizeBytes': 1024 * 1024,
           'modifiedAt': now, 'category': 'images'},
        ],
      });
      expect(group.wastedBytes, equals(2 * 1024 * 1024));
      expect(group.isHashConfirmed, isFalse);
    });

    test('isHashConfirmed is true when contentHash is non-null', () {
      final group = DuplicateGroup.fromMap({
        'sizeBytes': 100,
        'contentHash': 'abc123',
        'files': [],
      });
      expect(group.isHashConfirmed, isTrue);
    });

    test('wastedBytes is 0 for single file group', () {
      final now = DateTime.now().millisecondsSinceEpoch;
      final group = DuplicateGroup.fromMap({
        'sizeBytes': 500,
        'files': [
          {'path': '/x', 'name': 'x', 'sizeBytes': 500,
           'modifiedAt': now, 'category': 'other'},
        ],
      });
      expect(group.wastedBytes, equals(0));
    });
  });

  group('formatBytes', () {
    test('0 bytes', () => expect(formatBytes(0), equals('0 B')));
    test('512 bytes', () => expect(formatBytes(512), equals('512 B')));
    test('1 KB', () => expect(formatBytes(1024), equals('1.0 KB')));
    test('1 MB', () => expect(formatBytes(1024 * 1024), equals('1.0 MB')));
    test('1 GB', () => expect(formatBytes(1024 * 1024 * 1024), equals('1.0 GB')));
    test('1.5 MB', () {
      expect(formatBytes((1.5 * 1024 * 1024).round()), equals('1.5 MB'));
    });
    test('negative treated as 0', () => expect(formatBytes(-1), equals('0 B')));
  });
}
