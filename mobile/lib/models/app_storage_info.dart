/// Per-app storage breakdown.
class AppStorageInfo {
  final String packageName;
  final String appName;
  final int appBytes;
  final int dataBytes;
  final int cacheBytes;
  /// True when this data was fetched via StorageStatsManager (API 26+).
  /// False means it was estimated or unavailable.
  final bool isAccurate;

  const AppStorageInfo({
    required this.packageName,
    required this.appName,
    required this.appBytes,
    required this.dataBytes,
    required this.cacheBytes,
    required this.isAccurate,
  });

  int get totalBytes => appBytes + dataBytes + cacheBytes;

  factory AppStorageInfo.fromMap(Map<dynamic, dynamic> map) {
    return AppStorageInfo(
      packageName: map['packageName'] as String? ?? '',
      appName: map['appName'] as String? ?? '',
      appBytes: (map['appBytes'] as num?)?.toInt() ?? 0,
      dataBytes: (map['dataBytes'] as num?)?.toInt() ?? 0,
      cacheBytes: (map['cacheBytes'] as num?)?.toInt() ?? 0,
      isAccurate: map['isAccurate'] as bool? ?? false,
    );
  }

  @override
  String toString() =>
      'AppStorageInfo(name: $appName, total: $totalBytes, accurate: $isAccurate)';
}
