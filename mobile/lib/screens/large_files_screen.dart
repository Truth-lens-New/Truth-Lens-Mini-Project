import 'package:flutter/material.dart';
import '../models/file_item.dart';
import '../services/storage_scan_service.dart';
import '../widgets/file_list_item.dart';

/// Screen listing the largest files found on the device.
class LargeFilesScreen extends StatefulWidget {
  final StorageScanService scanService;

  const LargeFilesScreen({super.key, required this.scanService});

  @override
  State<LargeFilesScreen> createState() => _LargeFilesScreenState();
}

class _LargeFilesScreenState extends State<LargeFilesScreen> {
  List<FileItem> _files = [];
  bool _loading = true;
  String? _error;
  final Set<String> _pendingDelete = {};

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final files = await widget.scanService.getLargeFiles(limit: 100);
      if (mounted) {
        setState(() {
          _files = files;
          _loading = false;
        });
      }
    } on StorageScanException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _loading = false;
        });
      }
    }
  }

  Future<void> _confirmDelete(FileItem file) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete file?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(file.name),
            const SizedBox(height: 4),
            Text(
              file.path,
              style: Theme.of(ctx).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'This action is permanent and cannot be undone.',
              style: TextStyle(color: Colors.red),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _pendingDelete.add(file.path));
    try {
      final result = await widget.scanService.deleteFile(file.path);
      if (!mounted) return;
      if (result.success) {
        setState(() => _files.removeWhere((f) => f.path == file.path));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('File deleted successfully.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content:
                  Text(result.message ?? 'Could not delete this file.')),
        );
      }
    } on StorageScanException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _pendingDelete.remove(file.path));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Large Files'),
        actions: [
          IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh',
              onPressed: _loadData),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _files.isEmpty
                  ? const Center(child: Text('No large files found.'))
                  : RefreshIndicator(
                      onRefresh: _loadData,
                      child: ListView.separated(
                        itemCount: _files.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, i) {
                          final file = _files[i];
                          if (_pendingDelete.contains(file.path)) {
                            return const ListTile(
                              trailing: SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2),
                              ),
                              title: Text('Deleting...'),
                            );
                          }
                          return FileListItem(
                            file: file,
                            showDeleteAction: true,
                            onDelete: () => _confirmDelete(file),
                          );
                        },
                      ),
                    ),
    );
  }
}
