/// Formats a byte count into a human-readable string (e.g. "1.2 GB").
String formatBytes(int bytes, {int decimals = 1}) {
  if (bytes <= 0) return '0 B';
  const suffixes = ['B', 'KB', 'MB', 'GB', 'TB'];
  var value = bytes.toDouble();
  var index = 0;
  while (value >= 1024 && index < suffixes.length - 1) {
    value /= 1024;
    index++;
  }
  if (index == 0) return '${bytes} B';
  return '${value.toStringAsFixed(decimals)} ${suffixes[index]}';
}
