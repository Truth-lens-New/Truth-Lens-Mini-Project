import 'package:flutter/material.dart';
import '../models/storage_category.dart';
import '../utils/format_bytes.dart';

/// Card widget for a single storage category shown on the dashboard.
class CategoryCard extends StatelessWidget {
  final StorageCategory category;
  final int totalStorageBytes;
  final VoidCallback? onTap;

  const CategoryCard({
    super.key,
    required this.category,
    required this.totalStorageBytes,
    this.onTap,
  });

  static const _categoryColors = <StorageCategoryType, Color>{
    StorageCategoryType.images: Color(0xFF4CAF50),
    StorageCategoryType.videos: Color(0xFF2196F3),
    StorageCategoryType.audio: Color(0xFF9C27B0),
    StorageCategoryType.documents: Color(0xFFFF9800),
    StorageCategoryType.apps: Color(0xFFF44336),
    StorageCategoryType.cache: Color(0xFF607D8B),
    StorageCategoryType.other: Color(0xFF795548),
  };

  static const _categoryIcons = <StorageCategoryType, IconData>{
    StorageCategoryType.images: Icons.image_outlined,
    StorageCategoryType.videos: Icons.videocam_outlined,
    StorageCategoryType.audio: Icons.audiotrack_outlined,
    StorageCategoryType.documents: Icons.description_outlined,
    StorageCategoryType.apps: Icons.apps_outlined,
    StorageCategoryType.cache: Icons.cached_outlined,
    StorageCategoryType.other: Icons.folder_outlined,
  };

  @override
  Widget build(BuildContext context) {
    final color = _categoryColors[category.type] ?? Colors.grey;
    final icon = _categoryIcons[category.type] ?? Icons.folder;
    final fraction = totalStorageBytes > 0
        ? category.totalBytes / totalStorageBytes
        : 0.0;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 18,
                    backgroundColor: color.withOpacity(0.15),
                    child: Icon(icon, color: color, size: 20),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      category.type.label,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              LinearProgressIndicator(
                value: fraction.clamp(0.0, 1.0),
                backgroundColor: color.withOpacity(0.1),
                valueColor: AlwaysStoppedAnimation<Color>(color),
                minHeight: 4,
                borderRadius: BorderRadius.circular(2),
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    formatBytes(category.totalBytes),
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: color,
                    ),
                  ),
                  Text(
                    '${category.fileCount} files',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
