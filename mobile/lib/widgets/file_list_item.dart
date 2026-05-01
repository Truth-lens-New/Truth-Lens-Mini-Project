import 'package:flutter/material.dart';
import '../models/file_item.dart';
import '../utils/format_bytes.dart';

/// List tile representing a single file in large-files or explorer views.
class FileListItem extends StatelessWidget {
  final FileItem file;
  final VoidCallback? onDelete;
  final bool showDeleteAction;

  const FileListItem({
    super.key,
    required this.file,
    this.onDelete,
    this.showDeleteAction = false,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: const Icon(Icons.insert_drive_file_outlined),
      title: Text(
        file.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            file.path,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Text(
            _formatDate(file.modifiedAt),
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            formatBytes(file.sizeBytes),
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          if (showDeleteAction) ...[
            const SizedBox(width: 4),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.red),
              tooltip: 'Delete file',
              onPressed: onDelete,
            ),
          ],
        ],
      ),
      isThreeLine: true,
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${_p(dt.month)}-${_p(dt.day)} '
        '${_p(dt.hour)}:${_p(dt.minute)}';
  }

  String _p(int n) => n.toString().padLeft(2, '0');
}
