import 'package:flutter/material.dart';
import '../utils/format_bytes.dart';

/// Horizontal bar showing used vs free storage with labels.
class StorageBar extends StatelessWidget {
  final int usedBytes;
  final int totalBytes;

  const StorageBar({
    super.key,
    required this.usedBytes,
    required this.totalBytes,
  });

  @override
  Widget build(BuildContext context) {
    final fraction =
        totalBytes > 0 ? (usedBytes / totalBytes).clamp(0.0, 1.0) : 0.0;
    final freeBytes = totalBytes - usedBytes;

    Color barColor;
    if (fraction > 0.9) {
      barColor = Colors.red;
    } else if (fraction > 0.7) {
      barColor = Colors.orange;
    } else {
      barColor = Colors.blue;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(
            value: fraction,
            minHeight: 12,
            backgroundColor: Colors.grey.shade200,
            valueColor: AlwaysStoppedAnimation<Color>(barColor),
          ),
        ),
        const SizedBox(height: 6),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${formatBytes(usedBytes)} used',
              style: TextStyle(
                  fontSize: 12, color: barColor, fontWeight: FontWeight.w600),
            ),
            Text(
              '${formatBytes(freeBytes)} free',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            Text(
              formatBytes(totalBytes),
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ],
    );
  }
}
