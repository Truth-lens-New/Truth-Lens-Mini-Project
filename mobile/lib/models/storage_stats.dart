/// Represents overall device storage statistics.
class StorageStats {
  final int totalBytes;
  final int availableBytes;
  final int usedBytes;

  const StorageStats({
    required this.totalBytes,
    required this.availableBytes,
    required this.usedBytes,
  });

  factory StorageStats.fromMap(Map<dynamic, dynamic> map) {
    final total = (map['totalBytes'] as num?)?.toInt() ?? 0;
    final available = (map['availableBytes'] as num?)?.toInt() ?? 0;
    return StorageStats(
      totalBytes: total,
      availableBytes: available,
      usedBytes: total - available,
    );
  }

  double get usedFraction => totalBytes > 0 ? usedBytes / totalBytes : 0.0;

  @override
  String toString() =>
      'StorageStats(total: $totalBytes, available: $availableBytes, used: $usedBytes)';
}
